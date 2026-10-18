Generated standalone training policies live here locally. Their parameter
vectors and source hashes are registered in `docs/nova-1/generation-*-registration.json`.
The final evidence archive retains every source snapshot alongside its native
results; it avoids duplicating the shared controller hundreds of times in Git.

Use `python tools/nova/rebuild_population.py --out /workspace/work/nova-rebuilt`
to reconstruct and hash-check every registered policy independently. The final
submission candidate is the separate `experiments/nova-1/team.py`.
