param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("blue", "green")]
    [string]$Color
)

kubectl patch service aceest-live -n aceest --type merge -p "{`"spec`":{`"selector`":{`"app`":`"aceest-fitness`",`"color`":`"$Color`"}}}"
kubectl rollout status deployment/aceest-$Color -n aceest --timeout=120s
