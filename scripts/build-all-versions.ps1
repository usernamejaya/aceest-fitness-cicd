param(
    [string]$Image = "usernamejaya/aceest-fitness"
)

$versions = @(
    "1.0", "1.1", "1.1.2", "2.0.1", "2.1.2",
    "2.2.1", "2.2.4", "3.0.1", "3.1.2", "3.2.4"
)

foreach ($version in $versions) {
    docker build --build-arg APP_VERSION=$version -t "${Image}:${version}" .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    docker push "${Image}:${version}"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
