# ==============================================================================
# scripts/security-guard.ps1 — Motor Determinista de Guardrails y Seguridad
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 15: Guardrails / Seguridad Ejecutable)
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function bt([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

# ------------------------------------------------------------------------------
# 1. Verificación Canónica de Rutas del Workspace (Path Guard)
# ------------------------------------------------------------------------------
function Test-WorkspacePathGuard {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetFilePath,

        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath,

        [Parameter(Mandatory = $false)]
        [string]$Operation = "WRITE",

        [Parameter(Mandatory = $false)]
        [string[]]$AllowedInfrastructurePaths = @()
    )

    try {
        if ([string]::IsNullOrWhiteSpace($TargetFilePath)) {
            return [PSCustomObject]@{ Allowed = $false; Reason = "BLOCKED_EMPTY_PATH"; Detail = "Ruta objetivo vacía." }
        }

        # Resolver workspace canónico
        $canonWorkspace = (Resolve-Path -LiteralPath $WorkspacePath -ErrorAction Stop).Path.TrimEnd('\')

        # Resolver ruta objetivo absoluta
        $combinedTarget = if ([System.IO.Path]::IsPathRooted($TargetFilePath)) {
            $TargetFilePath
        } else {
            Join-Path $canonWorkspace $TargetFilePath
        }

        # Normalizar sin .. ni .
        $fullTarget = [System.IO.Path]::GetFullPath($combinedTarget).TrimEnd('\')

        # Comprobar si apunta o desciende por Junction / Symlink
        $checkParent = $fullTarget
        while (-not [string]::IsNullOrWhiteSpace($checkParent) -and -not (Test-Path -LiteralPath $checkParent)) {
            $checkParent = Split-Path -Parent $checkParent
        }

        if (Test-Path -LiteralPath $checkParent) {
            $item = Get-Item -LiteralPath $checkParent -Force -ErrorAction SilentlyContinue
            if ($item -and $item.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint)) {
                # Resolver destino real del symlink o junction
                $linkTarget = $item.Target
                if ($linkTarget) {
                    $linkResolved = [System.IO.Path]::GetFullPath($linkTarget).TrimEnd('\')
                    if (-not $linkResolved.StartsWith($canonWorkspace, [System.StringComparison]::OrdinalIgnoreCase)) {
                        return [PSCustomObject]@{
                            Allowed   = $false
                            Reason    = "BLOCKED_PATH_ESCAPE"
                            Target    = $fullTarget
                            Detail    = "ReparsePoint/Junction '$checkParent' escapa a destino fuera del workspace: '$linkResolved'"
                        }
                    }
                }
            }
        }

        # Comprobar si el path destino intenta destruir la raíz misma del proyecto
        if ($fullTarget.Equals($canonWorkspace, [System.StringComparison]::OrdinalIgnoreCase) -and ($Operation -eq "DELETE" -or $Operation -eq "DESTROY")) {
            return [PSCustomObject]@{
                Allowed   = $false
                Reason    = "BLOCKED_ROOT_DESTRUCTION"
                Target    = $fullTarget
                Detail    = "Intento de eliminación o sobreescritura destructiva de la raíz del proyecto."
            }
        }

        # Comprobar si la ruta objetivo está dentro del workspace
        $isInside = $fullTarget.StartsWith($canonWorkspace, [System.StringComparison]::OrdinalIgnoreCase)
        if (-not $isInside) {
            # Verificar si coincide con alguna excepción de infraestructura explícita
            $isInfraAllowed = $false
            foreach ($aPath in $AllowedInfrastructurePaths) {
                if (-not [string]::IsNullOrWhiteSpace($aPath)) {
                    $fullAllowed = [System.IO.Path]::GetFullPath($aPath).TrimEnd('\')
                    if ($fullTarget.StartsWith($fullAllowed, [System.StringComparison]::OrdinalIgnoreCase)) {
                        $isInfraAllowed = $true
                        break
                    }
                }
            }

            if ($isInfraAllowed) {
                return [PSCustomObject]@{
                    Allowed   = $true
                    Reason    = "ALLOWED_INFRASTRUCTURE_PATH"
                    Target    = $fullTarget
                    Detail    = "Ruta perteneciente a infraestructura permitida gestionada."
                }
            }

            return [PSCustomObject]@{
                Allowed   = $false
                Reason    = "BLOCKED_PATH_ESCAPE"
                Target    = $fullTarget
                Detail    = "Ruta fuera del workspace canónico: '$fullTarget' no pertenece a '$canonWorkspace'"
            }
        }

        return [PSCustomObject]@{
            Allowed   = $true
            Reason    = "ALLOWED_WORKSPACE_PATH"
            Target    = $fullTarget
            Detail    = "Ruta validada dentro del workspace canónico."
        }
    } catch {
        return [PSCustomObject]@{
            Allowed = $false
            Reason  = "BLOCKED_PATH_ERROR"
            Detail  = "Error resolviendo ruta canónica: $_"
        }
    }
}

# ------------------------------------------------------------------------------
# 2. Evaluación Determinista de Comandos Shell (Command Guard)
# ------------------------------------------------------------------------------
function Test-CommandGuard {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandLine,

        [Parameter(Mandatory = $false)]
        [string]$WorkspacePath = ""
    )

    if ([string]::IsNullOrWhiteSpace($CommandLine)) {
        return [PSCustomObject]@{ Allowed = $true; Reason = "EMPTY_COMMAND" }
    }

    # Normalización del comando
    $norm = $CommandLine.Trim()
    $normLower = $norm.ToLowerInvariant()
    $normLower = [System.Text.RegularExpressions.Regex]::Replace($normLower, '\s+', ' ')

    # 1. Detección de operaciones remotas o destructivas de Git
    if ($normLower -match '\bgit\s+push\b') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "git push hacia repositorio remoto está terminantemente prohibido."
            Rule           = "GIT_PUSH_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    if ($normLower -match '\bgit\s+clean\s+-[a-z0-9]*f') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "git clean destructivo (-f / -fdx) está bloqueado por seguridad."
            Rule           = "GIT_CLEAN_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    if ($normLower -match '\bgit\s+reset\s+--hard\b') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "git reset --hard destructivo está bloqueado."
            Rule           = "GIT_RESET_HARD_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    # 2. Detección de operaciones de partición o formato de discos
    if ($normLower -match '\b(format|diskpart|bcdedit)\b') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "Comando crítico de bajo nivel del sistema operativo bloqueado."
            Rule           = "DISK_SYSTEM_DESTRUCTION_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    # 3. Detección de modificación o borrado de Registry
    if ($normLower -match '\breg(\.exe)?\s+(delete|add|copy)\b' -or $normLower -match '\b(set-itemproperty|remove-itemproperty|remove-item)\b.*(hklm|hkcu):') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "Modificación del Registro de Windows bloqueada."
            Rule           = "REGISTRY_MODIFICATION_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    # 4. Detección de apagado o reinicio del sistema
    if ($normLower -match '\b(shutdown|restart-computer|stop-computer)\b') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "Apagado o reinicio del equipo bloqueado."
            Rule           = "SYSTEM_POWER_ACTION_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    # 5. Detección de modificación de firewall de Windows
    if ($normLower -match '\bnetsh\s+advfirewall\b' -or $normLower -match '\b(set-netfirewallrule|new-netfirewallrule)\b') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "Modificación de reglas de Firewall de Windows bloqueada."
            Rule           = "FIREWALL_MODIFICATION_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    # 6. Detección de borrado masivo de la raíz o directorio actual
    if ($normLower -match '\b(rmdir|rd)\s+.*(\.|\.\.|\/|\\)' -or $normLower -match '\bremove-item\s+.*-recurse\s+.*(\.|\$pwd|\$workspace)') {
        return [PSCustomObject]@{
            Allowed        = $false
            Reason         = "BLOCKED_COMMAND"
            Detail         = "Intento de eliminación recursiva del directorio raíz o del proyecto."
            Rule           = "ROOT_DESTRUCTION_FORBIDDEN"
            ActionRequired = "BLOCKED_REQUIRES_HUMAN"
            Command        = $CommandLine
        }
    }

    return [PSCustomObject]@{
        Allowed = $true
        Reason  = "ALLOWED_COMMAND"
        Command = $CommandLine
    }
}

# ------------------------------------------------------------------------------
# 3. Combinación Restrictiva de Políticas (Policy Merge = INTERSECCIÓN)
# ------------------------------------------------------------------------------
function Merge-EffectiveSecurityPolicy {
    param(
        [Parameter(Mandatory = $true)]
        [object]$SecurityConfig,

        [Parameter(Mandatory = $true)]
        [object]$ContractConfig
    )

    # Principio: effective_permissions = INTERSECCIÓN (nunca UNIÓN)
    $allowPush = $false
    if ($SecurityConfig.git.allow_push -and $ContractConfig.git.allow_push) {
        $allowPush = $true
    }

    $allowForcePush = $false
    if ($SecurityConfig.git.allow_force_push -and $ContractConfig.git.allow_force_push) {
        $allowForcePush = $true
    }

    $allowOutsideWorkspace = $false
    if ($SecurityConfig.filesystem.allow_outside_workspace -and $ContractConfig.filesystem.allow_outside_workspace) {
        $allowOutsideWorkspace = $true
    }

    $allowDestructive = $false
    if ($SecurityConfig.filesystem.allow_destructive -and $ContractConfig.filesystem.allow_destructive) {
        $allowDestructive = $true
    }

    $secMax = if ($SecurityConfig.chatgpt.max_queries) { [int]$SecurityConfig.chatgpt.max_queries } else { 5 }
    $conMax = if ($ContractConfig.chatgpt.max_queries) { [int]$ContractConfig.chatgpt.max_queries } else { 5 }
    $maxChatGpt = [Math]::Min($secMax, $conMax)

    return [ordered]@{
        principle               = "INTERSECTION_ONLY"
        allow_git_push          = $allowPush
        allow_git_force_push    = $allowForcePush
        allow_outside_workspace = $allowOutsideWorkspace
        allow_destructive       = $allowDestructive
        chatgpt_enabled         = $chatgptEnabled
        max_chatgpt_queries     = $maxChatGpt
        policy_source           = "config/security.yaml (Master Overrides RUN-CONTRACT)"
    }
}

# ------------------------------------------------------------------------------
# 4. Prevención de Exfiltración de Secretos (Secret Exfiltration Guard)
# ------------------------------------------------------------------------------
function Protect-SecretExfiltration {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Content,

        [Parameter(Mandatory = $false)]
        [string]$ContextName = ""
    )

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return [PSCustomObject]@{
            Status        = "CLEAN"
            SanitizedText = ""
            LeaksCount    = 0
            Blocked       = $false
        }
    }

    $text = $Content
    $leaksCount = 0

    # Token de prueba explícito de la especificación
    if ($text -match 'TEST_SECRET_DO_NOT_LEAK_12345') {
        $leaksCount++
        $text = $text -replace 'TEST_SECRET_DO_NOT_LEAK_12345', '[REDACTED]'
    }

    # API Keys tipo OpenAI (sk-...)
    if ($text -match 'sk-[a-zA-Z0-9]{20,}') {
        $leaksCount++
        $text = [System.Text.RegularExpressions.Regex]::Replace($text, 'sk-[a-zA-Z0-9]{20,}', '[REDACTED]')
    }

    # Tokens de GitHub (ghp_...)
    if ($text -match 'ghp_[a-zA-Z0-9]{20,}') {
        $leaksCount++
        $text = [System.Text.RegularExpressions.Regex]::Replace($text, 'ghp_[a-zA-Z0-9]{20,}', '[REDACTED]')
    }

    # Asignaciones tipo password/secret
    if ($text -match '(?i)(api[_-]?key|password|secret|bearer)\s*[:=]\s*[^\s,;]+') {
        $leaksCount++
        $text = [System.Text.RegularExpressions.Regex]::Replace($text, '(?i)(api[_-]?key|password|secret|bearer)\s*[:=]\s*[^\s,;]+', '$1: [REDACTED]')
    }

    $blocked = ($leaksCount -gt 0)
    $statusStr = if ($blocked) { "BLOCKED_SECRET_EXFILTRATION" } else { "CLEAN" }
    return [PSCustomObject]@{
        Status        = $statusStr
        SanitizedText = $text
        LeaksCount    = $leaksCount
        Blocked       = $blocked
        Context       = $ContextName
    }
}
