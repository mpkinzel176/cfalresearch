<#!
  Downloads the public publication list from Michael P. Kinzel's Google Scholar
  profile and writes src/data/publications-raw.json. Run
  `python scripts/build_publications.py` afterward (or `npm run build`, which
  does not do this automatically) to regenerate the site's src/data/publications.json
  with authors split out, DOI cross-references, and research-area tags.
  This is also run by the scheduled GitHub Action in
  .github/workflows/update-publications.yml.
#>
[CmdletBinding()]
param(
  [string]$ProfileId = 'LI9BgQkAAAAJ',
  [int]$StartYear = (Get-Date).AddYears(-5).Year
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outputPath = Join-Path $root 'src/data/publications-raw.json'
$headers = @{ 'User-Agent' = 'Mozilla/5.0 (compatible; CFAL-publication-refresh/1.0)' }
$items = [System.Collections.Generic.List[object]]::new()
$start = 0

do {
  $uri = "https://scholar.google.com/citations?user=$ProfileId&hl=en&view_op=list_works&sortby=pubdate&cstart=$start&pagesize=100"
  $html = (Invoke-WebRequest -Uri $uri -Headers $headers -UseBasicParsing).Content
  $rows = [regex]::Matches($html, '(?s)<tr class="gsc_a_tr".*?</tr>')

  foreach ($rowMatch in $rows) {
    $row = $rowMatch.Value
    $yearText = [regex]::Match($row, 'class="gsc_a_y"[^>]*>\s*<span[^>]*>(.*?)</span>').Groups[1].Value
    $year = 0
    if (-not [int]::TryParse($yearText, [ref]$year)) { continue }
    if ($year -lt $StartYear) { continue }

    $titleMatch = [regex]::Match($row, '(?s)<a href="([^"]*)"[^>]*class="gsc_a_at"[^>]*>(.*?)</a>')
    $title = [System.Net.WebUtility]::HtmlDecode([regex]::Replace($titleMatch.Groups[2].Value, '<.*?>', '')).Trim()
    if ([string]::IsNullOrWhiteSpace($title)) { continue }
    $metadata = [regex]::Matches($row, '(?s)<div class="gs_gray">(.*?)</div>')
    $authors = if ($metadata.Count -gt 0) { [System.Net.WebUtility]::HtmlDecode([regex]::Replace($metadata[0].Groups[1].Value, '<.*?>', '')).Trim() } else { '' }
    $venue = if ($metadata.Count -gt 1) { [System.Net.WebUtility]::HtmlDecode([regex]::Replace($metadata[1].Groups[1].Value, '<.*?>', '')).Trim() } else { '' }
    $items.Add([pscustomobject]@{ year = $year; title = $title; authors = $authors; venue = $venue; url = "https://scholar.google.com$($titleMatch.Groups[1].Value -replace '&amp;', '&')" })
  }
  $start += $rows.Count
} while ($rows.Count -eq 100)

$orderedItems = @($items | Sort-Object -Property year -Descending)
$payload = [ordered]@{
  source = "https://scholar.google.com/citations?user=$ProfileId&hl=en"
  refreshedAt = (Get-Date).ToUniversalTime().ToString('o')
  startYear = $StartYear
  publications = $orderedItems
}

New-Item -ItemType Directory -Force -Path (Split-Path $outputPath) | Out-Null
$json = $payload | ConvertTo-Json -Depth 4
$json | Set-Content -Encoding utf8 $outputPath
Write-Host "Wrote $($items.Count) publications from $StartYear onward to $outputPath"
Write-Host "Now run: python scripts/build_publications.py"
