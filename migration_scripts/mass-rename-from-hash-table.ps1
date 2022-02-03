
$hash = @{
    "00000012.json" = "adhoc_select_options.json"
    "00000056.json" = "adhoc_gold_lost_string.json"
}

ForEach ($h in $hash.GetEnumerator()) {
    Move-Item -Path ".\json\_lang\en\$($h.Name)" -Destination ".\json\_lang\en\$($h.Value)"
    Move-Item -Path ".\json\_lang\ja\$($h.Name)" -Destination ".\json\_lang\ja\$($h.Value)"
    ((Get-Content -Path .\app\hex_dict.csv -Raw) -replace "json\\_lang\\en\\$($h.Name)", "json\_lang\en\$($h.Value)") | Set-Content -Path .\app\hex_dict.csv
}
