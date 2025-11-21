# Examples Directory

This directory contains a sample Cadence Allegro netlist file for testing and demonstration purposes.

## Files in This Directory

- **pstxnet_v3.dat** - Sample input netlist (~1.1KB)
- **diff_netlist.sh** - Script to compare generated output with reference file
- **.cnl_format.dat** - Configuration file (pre-configured to point to pstxnet_v3.dat)

Reference output file is located at: `../tests/data/expected/netlist_v3_expected.rpt`

## For Users: Try the Tool

If you want to see `cnl_format` in action:

1. Navigate to this directory:
   ```bash
   cd examples/
   ```

2. Run the tool:
   ```bash
   cnl_format
   ```

3. The GUI will automatically load `pstxnet_v3.dat` (configured via `.cnl_format.dat`)

4. Click "Format Netlist" to generate the report

5. The tool will create `NetList.rpt` with a formatted, human-readable report

6. Compare the generated output with the reference file:
   ```bash
   ./diff_netlist.sh
   ```
   Or manually:
   ```bash
   diff NetList.rpt ../tests/data/expected/netlist_v3_expected.rpt
   ```

## For Developers: Manual Testing

This directory serves as a manual testing workspace:

1. Run `cnl_format` in this directory
2. The config file `.cnl_format.dat` pre-selects `pstxnet_v3.dat` for testing
3. Click "Format Netlist" to generate `NetList.rpt`
4. Compare the generated output with the reference file:
   ```bash
   ./diff_netlist.sh
   ```
5. Use version control to verify output changes after code modifications

The tool will:
- Read `.cnl_format.dat` to remember the last file selection
- Generate `NetList.rpt` with the formatted netlist
- Auto-version old reports as `NetList.rpt,0`, `NetList.rpt,1`, etc.

## Automated Testing

For automated regression testing with multiple test cases, see the `tests/data/` directory.
