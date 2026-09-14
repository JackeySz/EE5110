# Source Module Instructions

- Preserve the public contracts in `docs/INTERFACES.md`.
- Keep modules acyclic and follow the dependency direction in `docs/ARCHITECTURE.md`.
- Validate public inputs; internal helpers may assume already validated data when clearly documented.
- Keep mathematical code free of OpenCV and filesystem dependencies.
- Keep CLI, video, and visualization concerns out of mathematical modules.
- An algorithm placeholder raises `NotImplementedError` only when called; imports must remain safe.
- New public symbols require documentation and an explicit interface decision.
- Use NumPy typing conservatively so Python 3.9 remains supported.
