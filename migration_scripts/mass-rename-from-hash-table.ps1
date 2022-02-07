
$hash = @{
    "57.json" = "locations_housing.json"
    "58.json" = "glamour.json"
}

$JsonPath = "..\json\_lang"

ForEach ($h in $hash.GetEnumerator()) {
        Move-Item -Path $JsonPath\en\$($h.Name) -Destination $JsonPath\en\$($h.Value)
        Move-Item -Path $JsonPath\ja\$($h.Name) -Destination $JsonPath\ja\$($h.Value)
        ((Get-Content -Path ..\app\hex_dict.csv -Raw) -replace "json\\_lang\\en\\$($h.Name)", "json\_lang\en\$($h.Value)") | Set-Content -Path ..\app\hex_dict.csv
}
