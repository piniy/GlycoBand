# Synthetic robustness configs

Create separate State and Trend degradation configs only after the corresponding predictive model and held-out policy are frozen.

- State degradation must begin from real held-out four-wavelength Hb-PPG.
- Trend degradation must begin from real held-out BIG IDEAs BVP.
- Preserve the original participant, source, chronology, and biological label.
- Never treat degraded samples as new people or physical-device validation.
