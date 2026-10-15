"""Relocate test OUTPUTS only; execute unchanged assertions against real sources.

Old phase scripts default to historical evidence paths. This adapter changes
only an explicit output-directory assignment and/or write_text/write_bytes
receivers. Input reads, guards, assertions, source paths and run logic remain.
The complete instrumented source and AST assertion equality are saved.
"""
from pathlib import Path
import argparse,ast,hashlib,json,os,sys
R=Path(__file__).resolve().parents[2]
if not(R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--test',required=True);ap.add_argument('--output',required=True);ap.add_argument('--directory',action='append',default=[]);ap.add_argument('--dry-run',action='store_true');args,remaining=ap.parse_known_args()
source=R/'tests'/args.test;assert source.is_file() and source.resolve().is_relative_to(R/'tests')
E=Path(args.output).resolve();assert E.is_relative_to(R/'evidence') or (args.dry_run and E.is_relative_to(R/'logs'));E.mkdir(parents=True,exist_ok=False)
raw=source.read_text(encoding='utf-8-sig');tree=ast.parse(raw,filename=str(source));before=[ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Assert)];edits=[]
def root_literal(node):
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div) and isinstance(node.left,ast.Name) and node.left.id in ['ROOT','R'] and isinstance(node.right,ast.Constant) and isinstance(node.right.value,str):return node.right.value
 return None
def target(name):return ast.parse(repr(str(E/name)),mode='eval').body
def output_path(name):return ast.Call(func=ast.Attribute(value=ast.Call(func=ast.Name(id='__import__',ctx=ast.Load()),args=[ast.Constant('pathlib')],keywords=[]),attr='Path',ctx=ast.Load()),args=[target(name)],keywords=[])
class OutputsOnly(ast.NodeTransformer):
 def visit_Assign(self,node):
  literal=root_literal(node.value)
  if literal in args.directory and all(isinstance(t,ast.Name) and t.id in ['E','e'] for t in node.targets):
   edits.append({'kind':'output_directory','line':node.lineno,'old':literal});node.value=output_path(Path(literal).name)
  return self.generic_visit(node)
 def visit_Call(self,node):
  if isinstance(node.func,ast.Attribute) and node.func.attr in ['write_text','write_bytes']:
   literal=root_literal(node.func.value)
   if literal and literal.startswith('evidence/'):
    edits.append({'kind':'write_receiver_only','line':node.lineno,'old':literal});node.func.value=output_path(Path(literal).name)
  return self.generic_visit(node)
tree=OutputsOnly().visit(tree);ast.fix_missing_locations(tree)
after=[ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,ast.Assert)]
assert before==after,'TEST_ASSERTION_MODIFICATION_DENIED'
assert edits,'NO_EXPECTED_OUTPUT_RELOCATION_FOUND'
for d in args.directory:(E/Path(d).name).mkdir(exist_ok=True)
instrumented=ast.unparse(tree)+'\n';(E/'instrumented-source.py.txt').write_text(instrumented,encoding='utf-8')
(E/'ADAPTER.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assertions_unchanged':True,'assertion_count':len(before),'edits':edits,'dry_run':args.dry_run},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if args.dry_run:print(json.dumps({'status':'ADAPTER_DRY_RUN_PASS','assertions':len(before),'edits':edits}));raise SystemExit(0)
sys.path.insert(0,str(R/'tests'));sys.argv=[str(source),*remaining]
exec(compile(tree,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
