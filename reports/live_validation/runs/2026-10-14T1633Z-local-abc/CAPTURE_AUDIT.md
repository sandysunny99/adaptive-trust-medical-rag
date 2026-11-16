# Source capture audit: REL-LIVE-0001 (simvastatin, clarithromycin)

Run folder: `reports/live_validation/runs/2026-10-14T1633Z-local-abc/`
Capture folder: `source_capture/` in this run folder.

REL-LIVE-0001 stays CANDIDATE_PENDING_RESEARCHER_APPROVAL. This audit records bytes and quotes only. It approves nothing and builds no candidate file.

## How the capture was run

```
.venv/Scripts/python.exe scripts/capture_live_relationship_sources.py --out reports/live_validation/runs/2026-10-14T1633Z-local-abc/source_capture
```

- Exit code 0. Status `COMPLETE`, 6 of 6 items `CAPTURED`, `failed: 0`. Full output: `capture_output.txt`.
- I used the script's own `--out` flag, without editing the script. Its default output folder is `data/live_medical/relationships/source_capture/<date>`, which sits inside `data/live_medical/**`, and nothing may be written there for this run. That default folder does not exist and was not created.
- No network, TLS or proxy errors.
- The downloaded files were read as data only. Nothing from them was executed.

## File integrity (recomputed against CAPTURE_MANIFEST.json)

| File | HTTP | Bytes (manifest = actual) | SHA-256 (manifest = actual) | Fetched (UTC) |
|---|---|---|---|---|
| spl_8f55d5de-5a4f-4a39-8c84-c53976dd6af9.xml | 200 | 222351 ✔ | `20a97640ddc74981ca41f3c0696d8a23ca3f3473236801fcc31b43825413bedb` ✔ | 2026-10-14T16:42:42 |
| spl_8f55d5de-5a4f-4a39-8c84-c53976dd6af9_history.json | 200 | 954 ✔ | `4a5da835b3e8f4f500efd568d303f0ec0ed054e866aff10b316ccf2d733c1f8e` ✔ | 16:42:44 |
| spl_9aaffb41-408c-4372-8fd5-1d649450c0e9.xml | 200 | 353750 ✔ | `628e25c7b3f433bf7be856c32c5eaa9e1179ae7069d1313571ff2ac320f7b04c` ✔ | 16:42:44 |
| spl_9aaffb41-408c-4372-8fd5-1d649450c0e9_history.json | 200 | 1459 ✔ | `0b56df14d456a25d6c15b6a2c7d64857f16165c70cdb48cca51fba183a5be19c` ✔ | 16:42:45 |
| rxnav_36567_properties.json | 200 | 122 ✔ | `da6e8725bf624cf882cb6c44ac0faa99965d19a0e4c16ee482daaa051e7f0910` ✔ | 16:42:45 |
| rxnav_21212_properties.json | 200 | 125 ✔ | `3ee1e690c54c4cff82ea0dd30e1e64bfb1fd32dbd4015dd78bf7c5983ec49c15` ✔ | 16:42:46 |

No mismatches and no missing files. (In my first audit pass, `capture_audit.json` shows `match: false`. That came from my script reading a size key the manifest doesn't use; the manifest's key is `bytes`. The second pass compared `bytes` and `sha256` directly, and all 6 match.)

## RxNav

| RxCUI | name | tty |
|---|---|---|
| 36567 | simvastatin | IN |
| 21212 | clarithromycin | IN |

## SPL documents

| Set ID | versionNumber | effectiveTime | Product title (from `<title>`, plain text) | DailyMed history |
|---|---|---|---|---|
| 9aaffb41-408c-4372-8fd5-1d649450c0e9 | 21 | 20231010 | "...CLARITHROMYCIN tablets, for oral use Initial U.S. Approval: 1991" (history title: CLARITHROMYCIN TABLET, FILM COATED [AUROBINDO PHARMA LIMITED]) | latest v21, published Nov 22, 2023 |
| 8f55d5de-5a4f-4a39-8c84-c53976dd6af9 | 11 | 20250328 | "...ZOCOR® (simvastatin) tablets, for oral use Initial U.S. Approval: 1991" (history title: ZOCOR (SIMVASTATIN) TABLET, FILM COATED [ORGANON LLC]) | latest v11, published Apr 03, 2025 |

**Version note (ZOCOR):** the script's `label_seen` for this set ID is "Revised 8/2023". DailyMed now serves version 11 with effectiveTime 20250328. The history lists v8 published Aug 23, 2023, so the label seen earlier was probably v8 and the capture is a later revision. The quoted Table 2 text below comes from v11. The clarithromycin label matches its `label_seen` ("Revised 10/2023" against effectiveTime 20231010).

## Clarithromycin, section 4.5 "Lomitapide, Lovastatin, and Simvastatin"

File `spl_9aaffb41-408c-4372-8fd5-1d649450c0e9.xml`. Offsets are 0-based byte offsets into the file, end exclusive.

Section title, bytes 75208–75266:

```xml
<title>4.5 Lomitapide, Lovastatin, and Simvastatin</title>
```

Contraindication paragraph, bytes 75723–76181, span SHA-256 `1bc9541f93d8836b01c1032df2794ab719b8064aa34abf38a22ee2fb7ecce874`. Raw XML, exactly as in the file (` ` marks one no-break space byte sequence, U+00A0):

```xml
<paragraph>Concomitant administration of clarithromycin tablets with HMG-CoA reductase inhibitors (statins) that are extensively metabolized by CYP3A4 (lovastatin or simvastatin) is contraindicated, due to the increased risk of myopathy, including rhabdomyolysis <content styleCode="italics">[see <linkHtml href="#Section_5.4">Warnings and Precautions (5.4)</linkHtml> and <linkHtml href="#Section_7">Drug Interactions (7)</linkHtml>]</content>.</paragraph>
```

Plain text after removing tags (entities decoded, whitespace collapsed):

> Concomitant administration of clarithromycin tablets with HMG-CoA reductase inhibitors (statins) that are extensively metabolized by CYP3A4 (lovastatin or simvastatin) is contraindicated, due to the increased risk of myopathy, including rhabdomyolysis [see Warnings and Precautions (5.4) and Drug Interactions (7)].

## ZOCOR Table 2, "Strong CYP3A4 inhibitors" row group

File `spl_8f55d5de-5a4f-4a39-8c84-c53976dd6af9.xml` (v11). The caption "Table 2: Drug Interactions that Increase the Risk of Myopathy and Rhabdomyolysis with ZOCOR" starts at character 87933, and the row group below follows it. In the source, the group is one heading row plus three `<tr>` rows. Byte offsets, end exclusive:

| Row | Bytes | Span SHA-256 | Plain text |
|---|---|---|---|
| Heading | 88294–88467 | `ebb9a9f0e49abae6…` | Strong CYP3A4 inhibitors |
| Clinical Impact | 88569–89124 | `723a4b37c33de6db…` | Simvastatin is a substrate of CYP3A4. Concomitant use of strong CYP3A4 inhibitors with ZOCOR increases simvastatin exposure and increases the risk of myopathy and rhabdomyolysis, particularly with higher ZOCOR dosages. |
| **Intervention** | **89155–89784** | `799fc0fd0b76268fd4084ed69cc517d663884270138ae677eec61372b5122721` | **Intervention: Concomitant use of strong CYP3A4 inhibitors with ZOCOR is contraindicated [see Contraindications (4)]. If treatment with a CYP3A4 inhibitor is unavoidable, suspend ZOCOR during the course of strong CYP3A4 inhibitor treatment.** |
| Examples | 89815–90508 | `7ed084e60c355858…` | Examples: Select azole anti-fungals (e.g., itraconazole, ketoconazole, posaconazole, and voriconazole), select macrolide antibiotics (e.g., erythromycin and clarithromycin), select HIV protease inhibitors (e.g., nelfinavir, ritonavir, and darunavir/ritonavir), select HCV protease inhibitors (e.g., boceprevir and telaprevir), cobicistat-containing products, and nefazodone. |

Raw XML of the Intervention row, exactly as in the file (indentation kept, ` ` = U+00A0):

```xml
<tr styleCode="Botrule">
                                 <td styleCode="Lrule Rrule" valign="middle">
                                    <content styleCode="italics">Intervention:   </content>
                                 </td>
                                 <td styleCode="Rrule">Concomitant use of strong CYP3A4 inhibitors with ZOCOR is contraindicated <content styleCode="italics">[see <linkHtml href="#S4">Contraindications (4)</linkHtml>]</content>. If treatment with a CYP3A4 inhibitor is unavoidable, suspend ZOCOR during the course of strong CYP3A4 inhibitor treatment.</td>
                              </tr>
```

**Note:** in ZOCOR, the sentence that states the contraindication names the class ("strong CYP3A4 inhibitors"), not clarithromycin. Clarithromycin appears only in the separate Examples row of the same group. Any record built from this label has to join the two rows; no single sentence states "simvastatin with clarithromycin is contraindicated". The clarithromycin label does name simvastatin directly (section 4.5 above).

Full spans with raw XML for every row: `capture_spans.json`. First-pass audit output: `capture_audit.json`.

## Problems found

- No access errors, missing files, or hash or size mismatches.
- ZOCOR version drift, as described above: label_seen says 8/2023, the capture is v11 with effectiveTime 20250328.
