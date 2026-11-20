# Rofental Sample FSM-OGGM Scripts

## Overview

This directory contains Python scripts for preparing, running, and analysing a sample glacier-modelling workflow that combines the Firn-Snowpack Model (FSM) with OGGM-related inputs and processing. The scripts are intended to be run as part of the Rofental example workflow and may depend on files created by earlier scripts.

This README excludes `generate_small_ensemble.py`.

## Requirements

- Python 3
- A working OGGM installation
- A working FSM-OGGM installation (path set via `fsm-oggm_path`)
- The Python packages imported by the individual scripts
- Access to the input datasets used by the workflow (WFDE5 climate data, WGMS database, RGI-WGMS lookup table)
- Sufficient disk space for intermediate and output files

Create a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install required packages:

    pip install -r requirements.txt

## Directory and path configuration

The workflow is configured through an `.ini`-style parameter file. Before running any script:

1. Open the configuration file and review every entry.
2. Update all paths (`working_dir`, `climate_file`, `wgms_path`, `wgms_to_rgi_path`, `parameter_sample_file_base`, `fsm-oggm_path`) for your own system. The example file contains paths specific to another user account and network location, which will not exist elsewhere.
3. Confirm referenced directories exist, or create them.

## Running a script

    python scripts/rofental_sample_FSM_OGGM/script_name.py

or:

    cd scripts/rofental_sample_FSM_OGGM
    python script_name.py

If a script accepts command-line arguments, display its help message first:

    python script_name.py --help

## Recommended workflow

1. Prepare or download the required input data.
2. Set up the configuration file for the target glacier and run type.
3. Generate or confirm the parameter sample file.
4. Run OGGM preprocessing and FSM forcing preparation.
5. Run the FSM simulations, as a full ensemble or a single sample.
6. Post-process and inspect model output.
7. Create plots, tables, or other summary products.

---

## Parameter file reference

The configuration file has five sections: `[General]`, `[OGGM]`, `[FSM_OGGM]`, `[InputData]`, and `[Output]`.

**Note on confidence levels:** entries marked *(confirmed)* are standard, documented OGGM/FSM parameters or have unambiguous roles. Entries marked *(inferred)* are reasonable interpretations based on naming conventions and the overall ensemble/calibration workflow design. They have not been verified against the FSM-OGGM source code and should be checked before being relied on for scientific work.

### [General]

| Parameter | Description |
|---|---|
| `working_dir` *(confirmed)* | Root directory for all outputs and intermediate files. |
| `reset` *(confirmed)* | `True` clears the working directory before running; `False` reuses existing output where possible. |

### [OGGM]

Standard, documented OGGM parameters *(confirmed)*.

| Parameter | Description |
|---|---|
| `use_multiprocessing` | Enables parallel execution of OGGM tasks. |
| `mp_processes` | Number of worker processes used when multiprocessing is enabled. |
| `border` | Number of grid pixels added around each glacier outline when building the local model domain. |

A larger `border` increases memory and runtime for every downstream step. A larger `mp_processes` increases peak memory demand, so on memory-limited systems a larger `border` may require a smaller `mp_processes`.

### [FSM_OGGM] — run control

| Parameter | Description |
|---|---|
| `fsm_save_runoff` | Whether FSM writes runoff output in addition to standard snow/mass-balance variables. |
| `fsm_runoff_frequency` | Temporal resolution of saved runoff (`D` = daily). No effect if `fsm_save_runoff = False`. |
| `fsm_spinup` | Whether FSM runs an initialisation period to reach equilibrium snow/firn states before the main simulation, rather than starting from prescribed initial conditions. |
| `fsm_interpolate_bnds` | Whether elevation-band values are interpolated smoothly (`True`) or treated as discrete steps (`False`). |
| `fsm_nbnds` | Number of elevation bands used to discretise the glacier. More bands give finer vertical resolution at higher computational cost. |
| `fsm-oggm_path` *(confirmed)* | Path to the local FSM-OGGM installation. |
| `cost_variance_expansion` *(inferred)* | Likely a multiplier applied to the variance term in the calibration cost function, controlling how strongly mismatches with observations are penalised. `None` uses the default variance. |

### [FSM_OGGM] — FSM physical parameters

Twelve parameters configure FSM's snow and ice surface scheme: `fsm_param_bstb`, `fsm_param_asmx`, `fsm_param_asmn`, `fsm_param_aice`, `fsm_param_plapse`, `fsm_param_pf`, `fsm_param_tlapse`, `fsm_param_sigmoiddscale`, `fsm_param_z0ic`, `fsm_param_z0sn`, `fsm_param_slctle`, `fsm_param_preclimit`.

**Likely meaning of each (confidence varies):**

- `asmx`, `asmn` *(moderate–high confidence)* — maximum and minimum snow albedo; match FSM's documented parameter set.
- `z0sn` *(moderate–high confidence)* — snow surface roughness length; matches FSM's documented parameter set.
- `z0ic`, `aice` *(inferred)* — likely ice surface roughness length and ice albedo, added for glacier applications since base FSM targets seasonal snow rather than ice.
- `plapse`, `tlapse` *(inferred)* — likely precipitation and temperature lapse rates used to distribute single-point climate forcing across elevation bands.
- `pf` *(inferred)* — likely a precipitation correction/scaling factor.
- `preclimit` *(inferred)* — likely a threshold or limit applied to precipitation input.
- `bstb`, `sigmoiddscale`, `slctle` *(uncertain)* — no confident interpretation from the name alone. `slctle` may be a switch between alternative process formulations; `sigmoiddscale` may relate to a sigmoid-shaped transition curve. Both unverified.

**How each parameter can be set, and what each setting does:**

| Setting | Effect |
|---|---|
| `None` | Parameter is not varied across the ensemble. Every ensemble member uses FSM's internal default or a project-level default. |
| A single numeric value | Parameter is fixed at that value for every ensemble member, overriding the default, but still not varied. |
| A list, e.g. `[min, max]` | Parameter becomes an **active, sampled dimension** of the ensemble. A different value is drawn for each of the `num_samples` ensemble members, most likely within the given bounds. Confirm the exact sampling method in the source code. |

**Important:** it is the number of parameters set to a *list* — not `None` or a fixed scalar — that determines the dimensionality of the space actually explored by the ensemble.

- If **no** parameters are set to lists, no FSM physical parameter varies across the ensemble, and `num_samples` may have no effect on FSM behaviour unless other quantities are varied elsewhere in the workflow. Check this directly against the sampling code.
- If **one or two** parameters are set to lists, this is a low-dimensional, targeted sensitivity or calibration exercise, typically used once dominant parameters have already been identified.
- If **many or all twelve** parameters are set to lists, this is a full global sensitivity analysis/calibration. Coverage per dimension decreases for a fixed `num_samples` as dimensionality increases. If the sampling design is Sobol/Saltelli-based (plausible given `num_samples = 1024 = 2^10`), the number of model runs required typically scales with the number of active parameters (e.g. roughly `num_samples × (2D + 2)`). Adding list-valued parameters can therefore multiply computational cost rather than simply add to it. Confirm this scaling in the sampling code before planning runtime.

Whenever the set of list-valued parameters changes, regenerate the parameter sample file by setting `overwrite_sample_file = True`, since an existing sample file will not match the new dimensionality.

### [InputData]

| Parameter | Description |
|---|---|
| `climate_file` *(confirmed)* | Path to the meteorological forcing dataset (WFDE5 reanalysis, regional subset). |
| `wgms_path` *(confirmed)* | Path to the WGMS Fluctuations of Glaciers (FOG) database, providing observed glaciological data for calibration/validation. |
| `wgms_to_rgi_path` *(confirmed)* | Path to a lookup table linking WGMS glacier IDs to RGI glacier IDs. |
| `parameter_sample_file_base` *(confirmed)* | Base path/filename for the generated or read parameter sample file. |
| `overwrite_sample_file` *(role confirmed)* | `False` reuses an existing sample file (needed for reproducibility); `True` regenerates it. Set to `True` whenever the set of sampled `fsm_param_*` parameters changes. |
| `y0`, `y1` *(confirmed)* | Start and end year of the simulation period. |
| `num_samples` *(role confirmed)* | Size of the parameter ensemble. Only meaningful if at least one `fsm_param_*` is set to a list. Larger values improve robustness at a roughly proportional (or greater, under Saltelli-style designs) cost in runtime. |
| `calibrate_to_mean` *(inferred)* | Likely toggles whether calibration targets the long-term mean of observations over `years_cost` (`True`) or individual annual values (`False`). |
| `one_off_sample` | Selects a single ensemble member by index to run instead of the full ensemble, useful for debugging. As long as this is not `None`, an ensemble will not be run. A positive integer `i` will evaluate cost for the `i`th row of the sample .csv file (there is no check that `i` corresponds to an existing row). A value of `-1` will evaluate the cost corresponding to the ensemble member with lowest cost. A value of `-2` will evaluate cost for the FSM parameter values specified in the parameter file. For sampled parameters, the first value specified in the parameter range given is used. |
| `years_cost` *(confirmed)* | List of years whose observations are used in the calibration cost function. |
| `glacier_wgms_id` *(confirmed)* | WGMS identifier of the specific glacier being modelled. |

### [Output]

| Parameter | Description |
|---|---|
| `simulation_name` *(confirmed)* | Suffix appended to output file/run names, used to distinguish configurations stored in the same `working_dir`. |

---

## Practical configuration patterns

- **Full sensitivity analysis/calibration**: set most or all `fsm_param_*` entries to `[min, max]` lists, set `one_off_sample = -2`, and set `overwrite_sample_file = True`. Expect runtime to scale with the number of active parameters, not just `num_samples`.
- **Targeted calibration**: set only the parameter(s) of interest to lists (e.g. `fsm_param_tlapse`, `fsm_param_pf`), leaving the rest at `None` or literature-informed fixed scalars.
- **Fixed, non-ensemble run**: leave all `fsm_param_*` entries at `None` or scalars; verify that `num_samples` is not being used for anything in this configuration.
- **Debugging a single run**: use `one_off_sample` to select a specific ensemble member, set `use_multiprocessing = False`, and set `reset = True` for a clean, reproducible test.
- **Rerunning an existing ensemble**: keep list bounds identical to when the sample file was generated, set `overwrite_sample_file = False`, and use `one_off_sample` to pick individual members as needed.

## Input-data checks

- Temperature units (°C vs Kelvin) and precipitation units/accumulation intervals in the climate forcing.
- Date ranges and calendar conventions consistent with `y0`/`y1`.
- Elevation units and vertical datum consistency between OGGM and FSM.
- Correct matching of `glacier_wgms_id` to the intended RGI glacier via `wgms_to_rgi_path`.
- NetCDF variable names, dimensions, and missing-value conventions.

## Output files

Outputs may include OGGM intermediate files, FSM forcing files, model restart files, snow/ice/firn time series, NetCDF model output, CSV summary files, figures, and logs, written under `working_dir` and labelled using `simulation_name`.

## Troubleshooting

**Import errors** — activate the intended environment and install the missing dependency; confirm `python` and `pip` refer to the same environment.

**File-not-found errors** — check that all paths in the configuration file have been updated for your system.

**Sample file mismatches** — if parameter bounds or the set of list-valued parameters has changed, set `overwrite_sample_file = True` rather than reusing an outdated sample file.

**Unexpectedly identical ensemble members** — if all `fsm_param_*` entries are `None` or scalars, confirm whether `num_samples` is actually varying anything in the current configuration.

**Memory or runtime problems** — reduce `border`, `mp_processes`, `num_samples`, or the number of list-valued parameters for an initial test before running the full configuration.

## Caveats

Several parameter meanings and sampling behaviours above are inferred from naming conventions and general ensemble-workflow design, not confirmed from the FSM-OGGM source code. Before using this workflow for scientific conclusions, verify:

- The exact sampling method applied to list-valued `fsm_param_*` entries.
- Whether `num_samples` is a fixed ensemble size or a base size multiplied internally (e.g. Saltelli-style) as more parameters are varied.
- The precise behaviour of `calibrate_to_mean` and `one_off_sample`.
- The physical meaning of `bstb`, `sigmoiddscale`, and `slctle`.

## License and citation

Follow the licence and citation requirements of the repository and of all external datasets and software used by the workflow, including OGGM, FSM, WFDE5, WGMS, and RGI.

