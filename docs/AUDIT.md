# Audit and acceptance checkpoint

Audited baseline: 6e8c8a3f70c947c8eb201b5d590cda0ec2061195. All tracked source,
launch, package, workflow, shell and documentation files were read.

Working evidence: six pure Python unit tests pass. No prior experiment logs,
checkpoints, maps, datasets or simulator trials exist in the baseline.
Existing documentation correctly avoids empirical performance claims.

Findings: flattened PoseArray forecasts discard IDs, horizons and source stamps;
receipt timestamps disguise stale sensors; best-effort scan publishers are
incompatible with reliable subscriptions; simulated time is not exposed in launch;
NaN commands can escape the gate; repeated detector messages can refresh stale
tracks; fixed forecast indexing silently assumes eight samples. Scan checking is
frontal only, so reverse/spinning motion is not protected. The SLAM probe checks
presence, not map growth, geometry, time consistency or actual exploration.
The install wrapper targets Ubuntu, whereas this executor is Debian 13.

Acceptance order:
1. Fail-closed finite/time checks, metadata interfaces, sensor QoS; regression tests.
2. Build both packages in real Jazzy and exercise ROS transport; record output.
3. Reproducible leakage-resistant trajectory loader, CV/GRU/LSTM/Transformer
   training/evaluation, explicit dataset provenance and actual checkpoints.
4. Custom robot simulation, live mapping, AMCL and Nav2 trial evidence.
5. Calibrated perception, recorded-trajectory actor replay, matched A/B/C/D trials.

A code implementation or passing unit test never satisfies simulator acceptance.
Every unexecuted research experiment: NOT EXECUTED — NO EXPERIMENTAL RESULT AVAILABLE.
