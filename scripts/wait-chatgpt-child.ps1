function Wait-ChatGptChild([Diagnostics.Process]$Child,[int]$ParentMilliseconds,[scriptblock]$Trace){
    if($ParentMilliseconds -lt 1){throw 'INVALID_PARENT_DEADLINE'}
    $exited=$Child.WaitForExit($ParentMilliseconds)
    if(-not $exited){
        if($Trace){& $Trace 'PARENT_TIMEOUT'}
        # This Process instance owns the exact child handle; never kill by name.
        try{$Child.Kill()}catch{if(-not $Child.HasExited){throw}}
        if(-not $Child.WaitForExit(3000)){throw 'BRIDGE_CHILD_CLEANUP_FAILED'}
        if($Trace){& $Trace 'CHILD_TERMINATED'}
    }
    return $exited
}
