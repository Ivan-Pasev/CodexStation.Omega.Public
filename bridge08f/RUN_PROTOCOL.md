# Omega Tier-A Restricted-Source Reproduction Bridge v0.8f

Purpose: define a runner/receipt membrane for repositories that are not copied into the public Omega repository.

A conforming runner must:
1. operate in an environment already authorized for the source repository;
2. checkout the exact pinned source commit in an isolated workspace;
3. verify the checked-out HEAD equals the declared source commit;
4. execute only the declared native commands;
5. not patch source files to obtain a passing result;
6. emit only a sanitized JSON receipt;
7. set source_tree_modified_for_test=false;
8. omit source text, archives, credentials, tokens, environment secrets, and file contents from the public receipt;
9. classify unavailable execution as HOLD;
10. preserve authority_delta=NONE.

Runner identity and source identity are separate. A runner commit may change while the source commit under test must remain pinned.

Digital.Fabrica.Core pin: c3e142d73ddbbcdfd5677aed242da3c6c52ae9e6
Commands: npm install --ignore-scripts; npm run typecheck; npm run build.
Scope: TYPECHECK_BUILD. The pinned tree contains no native test files.

CodexStation.HighestOne pin: a4f237aba8156d0bf6f1354457275de9a67ac21a
Commands: cd formal/lean; bash tools/bootstrap_and_check.sh.
Scope: LEAN_KERNEL_GATE.

neural-lattice pin: 57da881b28a5a4e924b900a18e2e59f3a202f6fe
Commands: npm install --ignore-scripts; npm run validate.
Scope: FULL_NATIVE_VALIDATE.

Only the sanitized receipt is admissible for public ingestion. A valid receipt proves only its declared execution scope.
