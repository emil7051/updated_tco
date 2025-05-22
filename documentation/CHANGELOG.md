## v1.2.0 – 2025-05-23 – Domain Decomposition Completed

### Removed
* `tco_app.src.calculations` monolith – replaced by cohesive domain packages:
  * `tco_app.domain.energy`
  * `tco_app.domain.finance`
  * `tco_app.domain.externalities`
  * `tco_app.domain.sensitivity`

All call-sites now import directly from these modules.  The temporary façade has been deleted; importing from `tco_app.src.calculations` will raise `ImportError`.

### Added
* New domain modules (see above) with unchanged public APIs.
* `documentation/CHANGELOG.md` – you are reading it.

### Migration guide
```
# before
from tco_app.src.calculations import calculate_energy_costs

# after
from tco_app.domain.energy import calculate_energy_costs
```

Update your notebooks/scripts accordingly.  The CLI and Streamlit UI have already been migrated. 