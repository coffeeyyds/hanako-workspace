$outputDir = "D:/Hanako/播客_用AI搞学术/audio"

$episodes = @(
    @{num=1;  url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lsOkOQz_qbByjVe8Cj8jIUm919p5.m4a"},
    @{num=2;  url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lt9LV2iGaduWEuS2nn_raroJ7G11.m4a"},
    @{num=3;  url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lhOVnaHItNIOY3rll0zWrXfUhx8f.m4a"},
    @{num=17; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lltjsCdRD0jZxcW59aZvyQ5Z2-SP.m4a"},
    @{num=18; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lg65nfLmEKpPP6B3T8ZuTgezzPu6.m4a"},
    @{num=19; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/loXPYMWBQYB3xsbmo8JXnlLcYbgU.m4a"},
    @{num=20; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lmQyObiUuYQdP4bPd_ye7Ad6te5e.m4a"},
    @{num=21; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lliMY7I7AGBzj6zU6GYoyk_lS_LW.m4a"},
    @{num=22; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lpWHYapKkg8louE0fu4yQVKyI1YU.m4a"},
    @{num=23; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lv2x9AVFMwC5VMCXXNFZtMaDhx1b.m4a"},
    @{num=24; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lhUaapcDNBcISIYvzwuVMcleTxWA.m4a"},
    @{num=25; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lvvCnPDTiYauF2fFqmlAyu0y46jY.m4a"},
    @{num=26; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lhFNuRUN_6vbLk3YX3nEZ_BehDBo.m4a"},
    @{num=27; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lnaq1H2Ru-YTqGIHc6rIw2Jb0JJi.m4a"},
    @{num=28; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lk4geCifTQHV3lbTZhFdL75R5oPA.m4a"},
    @{num=29; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/ljbyQWYcC3R6pCYyPo-3wDXmV1N8.m4a"},
    @{num=30; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/lhVBlAC-4_etoIT573uIzKFuzQ0I.m4a"},
    @{num=31; url="https://media.xyzcdn.net/69b900fdbac28157ebe2f170/ltLouwSVZDNyCLhA3ggZwdwJuOoO.m4a"}
)

foreach ($ep in $episodes) {
    $numStr = $ep.num.ToString("00")
    $outFile = Join-Path $outputDir "ep${numStr}.m4a"
    if (Test-Path $outFile) {
        Write-Host "[SKIP] ep${numStr} already exists"
        continue
    }
    Write-Host "[DL] ep${numStr}..."
    try {
        Invoke-WebRequest -Uri $ep.url -OutFile $outFile -ErrorAction Stop
        $size = (Get-Item $outFile).Length
        Write-Host "[OK] ep${numStr} ($size bytes)"
    } catch {
        Write-Host "[FAIL] ep${numStr}: $_"
    }
}

Write-Host "Done!"
