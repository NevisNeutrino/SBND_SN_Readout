# Beam Shutdown Test Plan  
## SN Data Content and Write Performance Validation

---

## Test 1: Verify SN `.dat` File Content (Metadata-Only Check)

**Objective**  
Confirm whether SN `.dat` files contain only metadata (no waveform payload) when using Production `sbndaq` stack

**Estimated Time**  
~30 minutes per version

### Procedure
1. Configure and run SN data acquisition with Production environment
1. Produce a short SN run.
1. Inspect generated `.dat` files:
   - Compare file sizes.
   - Examine file contents (hexdump or structured inspection).
   - Check for presence or absence of waveform data.
1. Document:
   - Whether files contain only metadata.
   - Any structural differences between the two versions.

### Expected Output
- File size comparison table.
- Confirmation of metadata-only content (Yes/No).
- Notes on any structural differences.

---

## Test 2: SN Write Speed Stability and Fragment Consistency

**Objective**
1. Determine whether SN write speed drops approximately one hour after the start of a run.
2. Verify whether `frame` and `fem` values are consistently:
   - `frame = 2`
   - `fem = 4230520`

**artdaq Version**
- `yufan-nevisteststand`

**Estimated Time**  
2–3 hours

### Procedure
1. Start a continuous SN run.
2. Monitor over time:
   - Write speed.
   - Disk I/O.
   - Fragment rate.
3. Record write rate periodically, with timestamps.
4. Pay particular attention to behavior around the ~1 hour mark.
5. Inspect fragments and confirm:
   - `frame` value consistency.
   - `fem` value consistency.
6. Check whether the write speed drop (if observed) correlates with any changes in fragment structure.

### Expected Output
- Write speed vs. time log or plot.
- Confirmation whether a write rate drop occurs.
- Table of observed `frame` and `fem` values.
- Notes on reproducibility.

---
