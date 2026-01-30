# Changelog

## [1.3.10] - 2026-01-30

### Changed

- Updated message definitions

## [1.3.9] - 2025-11-17

### Fixed

- Fixed variable length message `GNSSSATINF`

## [1.3.8] - 2025-11-05

### Added

- This changelog
- Definitions for many messages and parameters
- Defines for CANSTATUS2 message

### Changed

- Improvements for `ixcom.grep.read_file`
    - Changed `filename` argument to accept a path, a filehandle or bytes
    - Added arguments to select the messages that should be parsed (`only_msg_ids`, `only_msg_names`, `ignore_msg_ids`, `ignore_msg_names`)
    - Added argument `get_parameter_history` to parse all logged parameters not only the last occured of each type
    - Added argument `stack_varsize_arrays` to stack messages with variable size on one numpy structured array
    - Added argument `no_gpstime_on_varsize_arrays` to not calculate the gpstime field (small performance improvement)
    - Improved the gpstime calculation to be continuus over a week change (disableable with `no_week_handling` argument)
    - Improved memory usage

### Fixed

- Fixed wrong order in `IMU_FILTERED` message definition
- Fixed wrong order in `IPST` message definition
- Fixed parameter naming for `PARGNSS_ANTOFFSET` for different antennas
- Fixed parameter naming for `PAREKF_VMP` for different channels
- Fixed parameter naming for `PARXCOM_SERIALPORT` for different com ports