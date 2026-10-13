"""Central read-only physical path resolution for Windows workspace admission.

No prefix-string authorization. Unknown reparse tags, cycles, dangling links and
resolution failures deny by default. This does not pin handles across later IO.
"""
import argparse,base64,json,os,pathlib,stat,sys

MAX_REPARSE_HOPS=32

class PathDenied(ValueError):pass

def native_link_target(value):
    # Only filesystem-returned link targets may contain a kernel namespace prefix.
    if value.startswith('\\\\?\\UNC\\'):raise PathDenied('NETWORK_REPARSE_TARGET_DENIED')
    if value.startswith(('\\\\?\\','\\??\\')):value=value[4:]
    return value

def absolute(raw,base=None):
    if not isinstance(raw,(str,os.PathLike)) or not str(raw).strip() or '\x00' in str(raw):raise PathDenied('INVALID_PATH')
    p=pathlib.Path(raw)
    if p.drive.startswith('\\\\') or (p.drive and not p.is_absolute()) or (p.root and not p.drive):raise PathDenied('AMBIGUOUS_PATH_DENIED')
    for part in p.parts[1:] if p.is_absolute() else p.parts:
        if ':' in part or part.endswith((' ','.')) and part not in ('.','..'):raise PathDenied('AMBIGUOUS_PATH_DENIED')
    if not p.is_absolute():
        if base is None:raise PathDenied('ABSOLUTE_PATH_REQUIRED')
        p=pathlib.Path(base)/p
    return pathlib.Path(os.path.abspath(p))

def resolve_path(raw, *, base=None,reject_reparse=False,reject_traversal=False):
    if reject_traversal and '..' in pathlib.Path(raw).parts:raise PathDenied('PATH_TRAVERSAL_DENIED')
    requested=absolute(raw,base);links=[];visited=set()
    def walk(path):
        current=pathlib.Path(path.anchor)
        parts=path.parts[1:]
        for index,part in enumerate(parts):
            candidate=current/part
            try:info=candidate.lstat()
            except FileNotFoundError:
                # Canonicalize the closest existing ancestor before appending a
                # not-yet-created suffix. Existing files cannot be used as parents.
                if not current.is_dir():raise PathDenied('INVALID_EXISTING_ANCESTOR')
                current=current.resolve(strict=True)
                return current.joinpath(*parts[index:])
            except OSError:raise PathDenied('PATH_RESOLUTION_FAILED') from None
            reparse=stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)
            if reparse:
                if reject_reparse:raise PathDenied('REPARSE_POINT_DENIED')
                key=(info.st_dev,info.st_ino)
                if key in visited:raise PathDenied('REPARSE_CYCLE_DENIED')
                if len(links)>=MAX_REPARSE_HOPS:raise PathDenied('REPARSE_LIMIT_DENIED')
                visited.add(key)
                try:target=native_link_target(os.readlink(candidate))
                except (OSError,ValueError):raise PathDenied('UNSUPPORTED_REPARSE_DENIED') from None
                target=absolute(target,current)
                links.append({'entry':str(candidate),'target':str(target)})
                current=walk(target)
                if not current.exists():raise PathDenied('REPARSE_TARGET_MISSING')
            else:current=candidate
            if index<len(parts)-1 and not current.is_dir():raise PathDenied('INVALID_EXISTING_ANCESTOR')
        return current.resolve(strict=True)
    physical=walk(requested)
    return {'requested':str(requested),'physical':str(physical),'reparse_points':links}

def admit(request):
    workspace=resolve_path(request['workspace'],reject_reparse=True)
    root=pathlib.Path(workspace['physical'])
    if not root.is_dir():raise PathDenied('INVALID_WORKSPACE')
    target=resolve_path(request['target'],base=workspace['requested'])
    physical=pathlib.Path(target['physical'])
    result={'Allowed':False,'Decision':'DENY','Reason':'PATH_BOUNDARY_VIOLATION',
        'Target':str(physical),'Requested':target['requested'],'Workspace':str(root),
        'ReparsePoints':target['reparse_points'],'writes_performed':0}
    if physical==root and request.get('operation','WRITE').upper() in ('DELETE','DESTROY'):
        result['Reason']='BLOCKED_ROOT_DESTRUCTION';return result
    if physical.is_relative_to(root):
        result.update(Allowed=True,Decision='ALLOW',Reason='ALLOWED_WORKSPACE_PATH');return result
    for scope in request.get('infrastructure',[]):
        allowed=pathlib.Path(resolve_path(scope,reject_reparse=True)['physical'])
        if physical.is_relative_to(allowed):
            result.update(Allowed=True,Decision='ALLOW',Reason='ALLOWED_INFRASTRUCTURE_PATH');return result
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);a=ap.parse_args()
    try:result=admit(json.loads(base64.b64decode(a.request).decode('utf-8')))
    except (PathDenied,OSError,ValueError,KeyError,TypeError) as e:
        result={'Allowed':False,'Decision':'DENY','Reason':str(e) if isinstance(e,PathDenied) else 'PATH_RESOLUTION_FAILED','writes_performed':0}
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
