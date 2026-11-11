# SLAC Devices — PV Units Reference

Units sourced from `virtual-accelerator` action variable classes, the `slac_variable_config.yaml` build config, and device code docstrings. PVs marked **(?)** are best guesses from naming conventions and should be verified.

---

## Magnet — Quadrupole

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| BCTRL | kG | W | Control setpoint (integrated field) |
| BACT | kG | R | Readback (integrated field) |
| BDES | kG | W | Desired setpoint |
| BCON | kG | R | Configuration strength |
| BMIN | kG | R | Minimum field limit |
| BMAX | kG | R | Maximum field limit |
| CTRL | enum | R/W | Control state (Ready, TRIM, PERTURB, BCON_TO_BDES, ...) |

## Magnet — Solenoid

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| BCTRL | kG-m | W | Control setpoint (integrated field) |
| BACT | kG-m | R | Readback (integrated field) |
| BDES | kG-m | W | Desired setpoint |
| BCON | kG-m | R | Configuration strength |
| BMIN | kG-m | R | Minimum field limit |
| BMAX | kG-m | R | Maximum field limit |
| CTRL | enum | R/W | Control state |

## Magnet — Horizontal / Vertical Corrector

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| BCTRL | kG-m | W | Control setpoint (integrated field) |
| BACT | kG-m | R | Readback (integrated field) |
| BDES | kG-m | W | Desired setpoint |
| BCON | kG-m | R | Configuration strength |
| BMIN | kG-m | R | Minimum field limit |
| BMAX | kG-m | R | Maximum field limit |
| CTRL | enum | R/W | Control state |

## Magnet — SBend (Dipole)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| BCTRL | GeV/c | W | Momentum setpoint |
| BACT | GeV/c | R | Momentum readback |
| BDES | GeV/c | W | Desired momentum |
| BCON | GeV/c | R | Configuration momentum |
| BMIN | GeV/c | R | Minimum momentum limit |
| BMAX | GeV/c | R | Maximum momentum limit |
| CTRL | enum | R/W | Control state |

---

## BPM (Beam Position Monitor)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| X | mm | R | Horizontal beam position |
| Y | mm | R | Vertical beam position |
| TMIT | Nel | R | Beam intensity (transmitted charge) |

---

## Screen (Profile Monitor)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| Image:ArrayData | pixel counts | R | Raw image array |
| Image:ArraySize0_RBV | pixels | R | Image dimension 0 (columns) |
| Image:ArraySize1_RBV | pixels | R | Image dimension 1 (rows) |
| N_OF_COL | pixels | R | Number of image columns |
| N_OF_ROW | pixels | R | Number of image rows |
| N_OF_BITS | bits | R | Bit depth per pixel |
| RESOLUTION | um/pixel | R | Pixel-to-physical size conversion |
| PNEUMATIC | boolean (0/1) | W | Screen insertion control |
| X (centroid) | mm | R | Beam centroid X position |
| Y (centroid) | mm | R | Beam centroid Y position |

---

## TCAV (Transverse Deflecting Cavity)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| AREQ | MV | W | Amplitude request (setpoint) |
| ADES | MV | W | Amplitude desired |
| AMPL_W0CH0 | MV | R | Amplitude readback |
| PREQ | degrees | W | Phase request (setpoint) |
| PDES | degrees | W | Phase desired |
| PACT_AVGNT | degrees | R | Phase readback (averaged) |
| REFPOC | degrees | R/W | Reference phase offset |
| RF_ENABLE | enum | R/W | RF enable state |
| AFBENB | enum | R/W | Amplitude feedback enable |
| AFBST | enum | R | Amplitude feedback status |
| PFBENB | enum | R/W | Phase feedback enable |
| PFBST | enum | R | Phase feedback status |
| MODECFG | enum | R/W | Mode configuration (Disable, ACCEL, STDBY, ACCEL_STDBY) |

---

## Wire Scanner

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| MOTR | um | R/W | Motor position setpoint |
| MOTR.RBV | um | R | Motor position readback |
| MOTR.VELO | um/s | R/W | Scan speed |
| MOTR.VMAX | um/s | R | Maximum speed limit |
| MOTR.VBAS | um/s | R | Minimum speed limit |
| MPSSPEED | mm/s | R | MPS speed limit |
| SCANPULSES | counts | R/W | Number of data points to collect per profile |
| STARTSCAN | trigger (0/1) | W | Start scan command |
| MOTR.STOP | trigger (0/1) | W | Abort scan command |
| XWIREINNER | um | R/W | X plane inner scan limit |
| XWIREOUTER | um | R/W | X plane outer scan limit |
| YWIREINNER | um | R/W | Y plane inner scan limit |
| YWIREOUTER | um | R/W | Y plane outer scan limit |
| UWIREINNER | um | R/W | U plane inner scan limit |
| UWIREOUTER | um | R/W | U plane outer scan limit |
| USEXWIRE | boolean (0/1) | R/W | Enable X plane scanning |
| USEYWIRE | boolean (0/1) | R/W | Enable Y plane scanning |
| USEUWIRE | boolean (0/1) | R/W | Enable U plane scanning |
| XWIRESIZE | um | R | X wire thickness |
| YWIRESIZE | um | R | Y wire thickness |
| UWIRESIZE | um | R | U wire thickness |
| BEAMRATE | Hz | R | Current beam rate |
| INSTALLANGLE | degrees | R | Wire install angle |
| TEMPERATURE | F | R | RTD temperature |
| MOTR_HOMED_STS | boolean | R | Wire at home position |
| ENABLED | boolean| R | Wire scanner enabled state |
| MOTR_RETRACT | trigger (0/1) | W | Retract command |
| TIMEOUT | boolean | R/W | Timeout enable |
| MOTR_ON_STS | boolean | R/W | Motor torque enable |
| POSN | um | R | Encoder Position |

---

## ICT (Integrating Current Transformer)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| CHARGE_NC | nC | R | Bunch charge |

---

## Toroid

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| TMIT | Nel | R | Transmitted beam intensity |

---

## LBLM (Loss Beam Loss Monitor)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| GATEDINTEGRAL | counts | R | Gated integral (integrated loss signal) |
| I0_LOSS | counts | R | I0 loss value |
| FAST_AMP_GAIN | dimensionless | R/W | Amplifier gain |
| FAST_AMP_BYPASS | boolean | R/W | Bypass state |
| FAST | counts | R | Fast signal (via timing buffer) |

---

## PMT (Photomultiplier Tube)

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| QDCRAW | counts | R | Raw QDC (charge-to-digital converter) reading |

---

## Klystron (Bmad-only, not in slac-devices)

Included for completeness; these PVs are defined in `slac_variable_config.yaml` but the Klystron device type is not yet in `slac-devices`.

| PV Suffix | Unit | R/W | Description |
|-----------|------|-----|-------------|
| ENLD | MeV | W | Energy loaded |
| PACT | degrees | R | Phase actual |
| PDES | degrees | W | Phase desired |
| BEAMCODE1_STAT | enum | R | Beam code 1 status |
| BEAMCODE2_STAT | enum | R | Beam code 2 status |
