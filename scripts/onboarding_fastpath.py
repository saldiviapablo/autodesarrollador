"""Deterministic onboarding for React/Vite projects.

The user approves the objective and a safe execution boundary, NOT model-invented
implementation files or frozen guessed UI tests. Hermes still plans at runtime;
Qwen implements and writes executable project tests. A host-owned immutable
sanity guard ensures a real test runner was configured; an independent Reviewer
must assess actual objective coverage before Completion Gate can pass.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re


VERIFIER_SOURCE = r"""'use strict';
const fs = require('node:fs');
const path = require('node:path');
function fail(message) {
  console.error('AUTONOMY_TESTS_INVALID: ' + message);
  process.exit(1);
}
if (!fs.existsSync('package.json')) fail('package.json missing');
let pkg;
try { pkg = JSON.parse(fs.readFileSync('package.json', 'utf8')); }
catch (_) { fail('package.json is not valid JSON'); }
const script = String((pkg.scripts || {}).test || '').trim();
if (!script || /^(echo|exit|true|rem|#)\b/i.test(script) ||
    /^npm(?:\.cmd)?\s+run\s+build\b/i.test(script) ||
    /--passWithNoTests\b/i.test(script)) {
  fail('provide an executable non-trivial npm test script');
}
const candidates = [];
function scan(dir, depth) {
  if (depth > 6 || !fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
    if (entry.isSymbolicLink()) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!['node_modules', 'dist', '.git', '.autopilot'].includes(entry.name))
        scan(full, depth+1);
    } else if (entry.isFile() && /\.(test|spec)\.[cm]?[jt]sx?$/i.test(entry.name)) {
      candidates.push(full);
    }
  }
}
scan('src',0);
scan('tests',0);
if (!candidates.length) fail('create at least one .test/.spec file under src or tests');
const substantive = candidates.some(name => {
  const source = fs.readFileSync(name,'utf8');
  return source.length >= 80 &&
    /\b(test|it|describe|expect|assert(?:\.[A-Za-z]+)?)\s*\(/.test(source);
});
if (!substantive) fail('test files lack observable assertions');
console.log('AUTONOMY_TESTS_PRESENT');
"""


def supports(objective: str) -> bool:
    return bool(re.search(r'\breact\b', objective, re.I) and
                re.search(r'\bvite\b', objective, re.I))


def _research_needed(objective: str) -> bool:
    return bool(re.search(
        r'investig|fuentes|research|buscar\s+(?:en\s+)?(?:internet|web)|'
        r'informaci[oó]n\s+(?:actual|reciente)|avances\s+de\s+ia|'
        r'documentaci[oó]n\s+(?:actual|oficial)|'
        r'papers|noticias\s+actual', objective, re.I))


def compile_proposal(objective: str, project_root: str | Path) -> dict:
    if not supports(objective):
        raise ValueError('FASTPATH_UNSUPPORTED_STACK')
    project = Path(project_root)
    verifier = '__autonomy_verify.cjs'
    digest = hashlib.sha256(VERIFIER_SOURCE.encode('utf-8')).hexdigest()
    original = project / verifier
    if original.exists() and hashlib.sha256(original.read_bytes()).hexdigest() != digest:
        verifier = '__autonomy_verify_' + hashlib.sha256(objective.encode('utf-8')).hexdigest()[:12] + '.cjs'
        original = project / verifier
    if original.exists() and hashlib.sha256(original.read_bytes()).hexdigest() != digest:
        raise ValueError('HOST_VERIFIER_PATH_COLLISION')
    seeds = {} if original.exists() else {verifier: VERIFIER_SOURCE}
    research = _research_needed(objective)
    allowed = [
        'index.html', 'package.json', 'package-lock.json', 'README.md',
        '.gitignore', 'vite.config.ts', 'vite.config.js', 'tsconfig.json',
        'tsconfig.node.json', 'tsconfig.app.json', 'tailwind.config.ts',
        'tailwind.config.js', 'postcss.config.js', 'postcss.config.cjs',
        'eslint.config.js', 'eslint.config.mjs',
    ]
    plan = {
        'schema_version': '1.0',
        'backend': 'live',
        'task': (
            'Implementar el objetivo completo aprobado dentro del workspace. '
            'Crear pruebas automatizadas reales (.test/.spec) y un script npm test '
            'que las ejecute; no usar pruebas falsas ni echo PASS. Ejecutar y '
            'corregir npm test y npm run build antes de terminar. '
            'El Reviewer independiente validara el objetivo, el codigo y las pruebas.'
        ),
        'allowed_files': allowed,
        'write_scope': ['src/**', 'public/**', 'docs/**', 'dist/**', 'tests/**', 'assets/**'],
        'tests': [
            {'id':'worker-tests','argv':['npm','run','test'],'marker':'test','timeout_seconds':180},
            {'id':'test-authenticity','argv':['node',verifier],
             'marker':'AUTONOMY_TESTS_PRESENT','timeout_seconds':30}
        ],
        'builds': [
            {'id':'npm-build','argv':['npm','run','build'],
             'marker':'build','timeout_seconds':120}
        ],
        'criteria': [
            {'criterion':'El proyecto cumple el objetivo original y sus pruebas reales pasan; el Reviewer lo verifica independientemente.', 'test_id':'worker-tests'},
            {'criterion':'El proyecto compila y genera un build valido sin errores.', 'test_id':'npm-build'},
            {'criterion':'Hay pruebas reales implementadas por el Worker, no solo marcadores de exito.', 'test_id':'test-authenticity'}
        ],
        'artifacts': [
            {'path':'index.html','min_bytes':1},
            {'path':'package.json','min_bytes':1},
            {'path':'src/App.tsx','min_bytes':1}
        ],
        'immutable_files': [{'path':verifier,'sha256':digest}],
        'phase_timeout_seconds':300,
        'global_timeout_seconds':2700,
        'max_cycles':5,
        'restart_budget':2,
    }
    requirements=[]
    if research:
        plan['research'] = {
            'query': ('Buscar, contrastar y citar fuentes originales actuales del siguiente objetivo: '+
                      re.sub(r'\s+',' ',objective).strip())[:500],
            'max_results':10,
        }
        requirements = ['Investigar fuentes web actuales y verificables para el objetivo aprobado.']
        if 'docs/research.md' in objective:
            plan['artifacts'].append({'path':'docs/research.md','min_bytes':100})
            plan['criteria'].append({
                'criterion':'Investigacion documentada con fuentes y fechas verificables en docs/research.md; revision independiente.',
                'test_id':'worker-tests'
            })
    overview = {
        'objective_summary':'Proyecto React/Vite. Hermes supervisa; Qwen implementa, prueba y corrige bajo limites aprobados.',
        'tasks':[
            'Hermes organiza y supervisa el trabajo despues de la aprobacion.',
            'Qwen investiga cuando corresponde, implementa los componentes y crea pruebas reales.',
            'Runner ejecuta las pruebas y el build, da feedback y permite correcciones acotadas.',
            'Reviewer independiente verifica objetivos y calidad antes del Completion Gate.'
        ],
        'research_requirements':requirements,
        'restrictions':['Solo workspace autorizado; sin push ni despliegues; no modificar infraestructura.',
                        'Los tests del Worker se revisan despues de implementar; no hay tests UI inventados por Hermes.'],
        'web_policy':'governed_https' if research else 'none',
        'chatgpt_policy':'disabled',
        'git_policy':'local_only_no_push',
        'completion_policy':'native_gate_all_criteria_tests_build_artifacts_diff_state_reviewer_no_pending',
    }
    return {'plan':plan,'seed_files':seeds,'overview':overview}
