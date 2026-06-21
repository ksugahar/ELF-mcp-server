"""Public-safe workflow recipes for ELF/MAGIC analyses.

Recipes are compact decision cards. They intentionally contain no solver
outputs, benchmark numbers, private paths, or machine-local provenance.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElfRecipe:
    name: str
    title: str
    solver: str
    goal: str
    use_when: tuple[str, ...]
    tags: tuple[str, ...]
    elements: tuple[str, ...]
    pre: tuple[str, ...]
    sol: tuple[str, ...]
    outputs: tuple[str, ...]
    examples: tuple[str, ...]
    checks: tuple[str, ...]
    pitfalls: tuple[str, ...]
    next_steps: tuple[str, ...]


RECIPES: tuple[ElfRecipe, ...] = (
    ElfRecipe(
        name="pm_airgap_field",
        title="PM rotor air-gap field map",
        solver="MAGIC",
        goal="Compute open-circuit magnet field and Fourier-analyse B_r(theta).",
        use_when=(
            "You need PM-only air-gap B field before adding current or iron.",
            "You want to verify magnet polarity, rotor angle, or observation-point placement.",
        ),
        tags=("motor", "pm-magnet", "field-map", "air-gap", "fourier"),
        elements=("MWL*", "MWV*", "MCO*", "MJH*"),
        pre=("HBUN/HBCU/HBRM for magnet recoil data", "HBCN for demagnetization step", "VEC1/VEC3 for vector magnets"),
        sol=("SOL MOME", "SOL FIEL"),
        outputs=("M3GB or M1PB field records", "MagFilter2 field CSV when tabular data is needed"),
        examples=("elf_examples_playbook(feature='motor')", "elf_examples_search('HBRM MCO SOL FIEL')"),
        checks=(
            "Place probes in air, away from material boundaries.",
            "Run a PM-only case before adding soft iron or coils.",
            "Check sign convention with a known rotor angle.",
        ),
        pitfalls=(
            "MWL magnet direction follows element winding order.",
            "VEC3 does not rescue a wrongly wound MWL element.",
            "Near-boundary probes can be dominated by mesh/geometry error.",
        ),
        next_steps=("passive_flum_pickup", "maxwell_torque_surface", "linear_iron_boost"),
    ),
    ElfRecipe(
        name="passive_flum_pickup",
        title="Passive pickup coil flux linkage",
        solver="MAGIC",
        goal="Read flux linkage through a passive search or phase coil.",
        use_when=(
            "You need Phi(theta) for back-EMF.",
            "You need pickup-coil flux without driving that coil.",
        ),
        tags=("motor", "flux-linkage", "back-emf", "pickup", "mcl", "flum"),
        elements=("MCL8T", "MCL2T", "MCL1*"),
        pre=("COI1 for pickup turns and subdivisions", "AMP1 pickup current set to 0"),
        sol=("SOL MOME", "SOL FIXA", "FLUM <pickup_mid>"),
        outputs=("M1MF flux-linkage records in .mag", "Phi(theta) series for differentiation"),
        examples=("elf_examples_search('FLUM COI1 AMP1')", "elf_examples_playbook(feature='flux-linkage')"),
        checks=(
            "Confirm pickup orientation with a simple PM-only or current-only case.",
            "Sweep rotor angle and verify the expected sign changes.",
            "Differentiate Phi(theta) only after angle ordering is correct.",
        ),
        pitfalls=(
            "A pickup coil must still have COI1 even when AMP1 is zero.",
            "FLUM target/source arguments should not be confused.",
            "Do not put the pickup surface through magnet or iron boundaries.",
        ),
        next_steps=("mutual_flux_current_pickup", "ipm_ldlq_flux", "pm_airgap_field"),
    ),
    ElfRecipe(
        name="mutual_flux_current_pickup",
        title="Driven source coil to passive pickup mutual flux",
        solver="MAGIC",
        goal="Check current excitation, sign, and mutual flux between coils.",
        use_when=(
            "You need a clean coil-current unit test before adding magnets or iron.",
            "You want source-isolated linkage from one coil to another.",
        ),
        tags=("coil-current", "flux-linkage", "mutual-inductance", "pickup", "flum"),
        elements=("MCL8T", "MCL2T", "MCL1*"),
        pre=("COI1 on source and pickup material IDs", "AMP1 source nonzero", "AMP1 pickup set to 0"),
        sol=("SOL MOME", "SOL FIXA", "FLUM <pickup_mid> <nb3> <source_mid>"),
        outputs=("M1MF source-isolated flux linkage", "L or M from Phi / I"),
        examples=("elf_examples_search('COI1 AMP1 FLUM')",),
        checks=(
            "Run paired positive and negative current cases.",
            "Keep source and pickup material IDs separate.",
            "Start with air-only geometry before adding PM or iron.",
        ),
        pitfalls=(
            "Using FLUM without a source MID can include total linkage.",
            "COI1 subdivision limits apply even for simple checks.",
            "Current direction follows coil element orientation.",
        ),
        next_steps=("passive_flum_pickup", "ipm_ldlq_flux", "linear_iron_boost"),
    ),
    ElfRecipe(
        name="maxwell_torque_surface",
        title="Maxwell-stress force or torque surface",
        solver="MAGIC",
        goal="Integrate force or torque on a closed stress surface.",
        use_when=(
            "You need cogging torque, reluctance torque, or radial pull over an angle sweep.",
            "You want a surface-integral observable around a rotor/body.",
        ),
        tags=("motor", "maxwell-force", "torque", "cogging", "sweep", "stress-surface"),
        elements=("MCM4T", "MCM3T", "MCM2T"),
        pre=("Stress-surface material ID in air", "No coil current required unless studying current-on force"),
        sol=("SOL MOME", "SOL FORT", "SELM ON <mid> <mid> 1"),
        outputs=(".mao TOTAL row: area flux Fx Fy Fz Tx Ty Tz"),
        examples=("elf_examples_playbook(feature='maxwell-force')", "elf_usage('force_methods')"),
        checks=(
            "Use a closed surface that fully encloses the target body.",
            "Keep the surface in air and away from material boundaries.",
            "Check symmetry angles where torque should vanish.",
        ),
        pitfalls=(
            "Open or self-intersecting stress surfaces corrupt force balance.",
            "Selecting the wrong material ID gives irrelevant TOTAL rows.",
            "FORC and FORT are different force methods; do not mix their outputs.",
        ),
        next_steps=("pm_airgap_field", "linear_iron_boost", "ipm_ldlq_flux"),
    ),
    ElfRecipe(
        name="ipm_ldlq_flux",
        title="IPM phase flux and Ld/Lq workflow",
        solver="MAGIC",
        goal="Compare PM-only and current-on phase flux to form dq quantities.",
        use_when=(
            "You are working with IPM Motor1/Motor2 style examples.",
            "You need phase flux linkage, dq transform, or Ld/Lq extraction.",
        ),
        tags=("motor", "ipm", "ldlq", "flux-linkage", "current-on", "dq"),
        elements=("MCL*", "MWL*", "MMB*", "MOV1", "ORI1"),
        pre=("COI1 for phase windings", "AMP1 tables for three-phase current", "MOV1/ORI1 or model rotor rotation"),
        sol=("SOL MOME with TIME", "SOL FIXA at each step", "FLUM for each phase"),
        outputs=("M1MF phase flux records", "phase-current table", "dq-transformed flux"),
        examples=("elf_examples_get('magic/IPM/Motor1.mai')", "elf_examples_get('magic/IPM/Motor2.mai')"),
        checks=(
            "Compare PM-only and current-on runs on the same geometry.",
            "Verify Ia+Ib+Ic balance before interpreting dq values.",
            "Confirm the electrical-angle convention used for Park transform.",
        ),
        pitfalls=(
            "Mechanical and electrical angle are not always the same.",
            "Phase order/sign errors can look like saliency errors.",
            "Do not publish product-derived numeric Ld/Lq references in public docs.",
        ),
        next_steps=("passive_flum_pickup", "mutual_flux_current_pickup", "maxwell_torque_surface"),
    ),
    ElfRecipe(
        name="linear_iron_boost",
        title="Linear soft-iron field boost",
        solver="MAGIC",
        goal="Add a simple linear magnetic material and compare field changes.",
        use_when=(
            "You want to isolate stator/yoke reluctance effects before nonlinear B-H.",
            "You need a low-risk iron-on versus iron-off comparison.",
        ),
        tags=("soft-iron", "motor", "field-map", "bh-curve", "linear"),
        elements=("MMB8T", "MMP*", "MMS*"),
        pre=("HBUN/HBCU two-point linear B-H curve", "HBCN material assignment"),
        sol=("SOL MOME", "SOL FIEL", "optional SOL FORT"),
        outputs=("Air-gap field ratio", "field-map change", "force/torque change if FORT is used"),
        examples=("elf_examples_search('HBUN HBCU MMB')",),
        checks=(
            "Keep observation points identical between PM-only and iron-on cases.",
            "Start with a monotone linear curve before nonlinear steel.",
            "Check that B-H units are consistent.",
        ),
        pitfalls=(
            "Very high permeability can make mesh/contact defects visible.",
            "Boundary-touching probes give unstable ratios.",
            "Nonlinear convergence settings matter once real B-H curves are used.",
        ),
        next_steps=("pm_airgap_field", "maxwell_torque_surface", "convergence_nonlinear_bh"),
    ),
    ElfRecipe(
        name="sinusoidal_momc",
        title="Linear sinusoidal AC magnetic analysis",
        solver="MAGIC",
        goal="Run frequency-domain magnetic response with complex material/current data.",
        use_when=(
            "You need a linear harmonic response instead of transient time stepping.",
            "You want AC fields or complex flux linkage.",
        ),
        tags=("sinusoidal-ac", "momc", "frequency", "complex", "flux-linkage"),
        elements=("MCL*", "MAB*", "MAT*", "MBB*"),
        pre=("CMU1/CMU1I for complex permeability", "AMP1/AMP1I or VOL1/VOL1I", "OHM* when needed"),
        sol=("SOL MOMC", "FREQ", "SOL FIEL", "SOL FIXA"),
        outputs=("Complex field records", "complex M1MF flux linkage"),
        examples=("elf_usage('sinusoidal')", "elf_examples_playbook(feature='sinusoidal-ac')"),
        checks=(
            "Use linear material data; nonlinear B-H is not available in MOMC.",
            "After MOMC, only FIEL and FIXA are available.",
            "Check real/imaginary current and material signs.",
        ),
        pitfalls=(
            "FORT/FORC/FIXB are not MOMC post-blocks.",
            "Missing imaginary data can lead to input errors.",
            "Frequency too small may be rejected.",
        ),
        next_steps=("passive_flum_pickup", "eddy_current_time_domain"),
    ),
    ElfRecipe(
        name="eddy_current_time_domain",
        title="Time-domain eddy-current setup",
        solver="MAGIC",
        goal="Model conducting magnetic/nonmagnetic bodies with transient diffusion.",
        use_when=(
            "You need shielding, rotor conductor, or plate transient effects.",
            "You need induced current or Joule-loss-oriented post-processing.",
        ),
        tags=("eddy-current", "time-domain", "conducting-body", "ohm2", "transient"),
        elements=("MAB*", "MAT*", "MBB*"),
        pre=("OHM2 for resistivity", "TIME-dependent excitation or motion", "STED for steady motion when applicable"),
        sol=("SOL MOME with TIME", "EMFM when induced current is requested", "SOL FIEL"),
        outputs=("field versus time", "induced current records when requested"),
        examples=("elf_examples_playbook(feature='eddy-current')", "elf_usage('sted')"),
        checks=(
            "Start with a small number of time steps and inspect convergence.",
            "Check conductor thickness/mesh scale against diffusion depth.",
            "Confirm resistivity units and time-step scale.",
        ),
        pitfalls=(
            "Too-large time steps can hide diffusion dynamics.",
            "Missing OHM2 prevents conductor behavior.",
            "Moving conductor and PASS settings can conflict.",
        ),
        next_steps=("sinusoidal_momc", "linear_iron_boost"),
    ),
    ElfRecipe(
        name="convergence_nonlinear_bh",
        title="Nonlinear B-H convergence pattern",
        solver="MAGIC",
        goal="Stabilize nonlinear magnetic solves.",
        use_when=(
            "The solve has nonlinear steel and convergence is fragile.",
            "You need a repeatable NONL sequence before adding motion sweeps.",
        ),
        tags=("convergence", "nonlinear", "bh-curve", "steel", "solve-control"),
        elements=("MMB*", "MMP*", "MMS*", "MWL*"),
        pre=("Monotone B-H data", "Correct HBUN units", "HBCN assignments"),
        sol=("SOL MOME", "NONL negative Newton steps", "NONL positive final iterations", "DMEG"),
        outputs=(".mao iteration table", "material permeability updates", "field/force post-blocks after convergence"),
        examples=("elf_usage('convergence')", "elf_usage('bh_curves')"),
        checks=(
            "Check B-H data monotonicity before tuning NONL.",
            "Use simpler linear material to isolate geometry issues.",
            "Read the worst element/material in the iteration table.",
        ),
        pitfalls=(
            "Bad B-H units can look like solver failure.",
            "Newton-only sequences may be approximate.",
            "Geometry defects often appear as convergence defects.",
        ),
        next_steps=("linear_iron_boost", "maxwell_torque_surface"),
    ),
)


def list_recipes(tag: str | None = None, solver: str | None = None) -> list[ElfRecipe]:
    """Return recipes filtered by optional tag and solver."""
    tag_l = tag.lower() if tag else None
    solver_u = solver.upper() if solver else None
    out: list[ElfRecipe] = []
    for recipe in RECIPES:
        if solver_u and recipe.solver.upper() != solver_u:
            continue
        if tag_l and not any(tag_l in t.lower() for t in recipe.tags):
            continue
        out.append(recipe)
    return out


def get_recipe(name: str) -> ElfRecipe | None:
    """Find a recipe by exact name or unambiguous substring."""
    query = name.lower().strip()
    for recipe in RECIPES:
        if recipe.name.lower() == query:
            return recipe
    matches = [r for r in RECIPES if query and query in r.name.lower()]
    return matches[0] if len(matches) == 1 else None


def search_recipes(query: str, top_k: int = 5, tag: str | None = None, solver: str | None = None) -> list[tuple[int, ElfRecipe]]:
    """Simple keyword search over public-safe recipe fields."""
    words = [w.lower() for w in query.split() if w.strip()]
    scored: list[tuple[int, ElfRecipe]] = []
    for recipe in list_recipes(tag=tag, solver=solver):
        hay_parts = [
            recipe.name,
            recipe.title,
            recipe.goal,
            " ".join(recipe.use_when),
            " ".join(recipe.tags),
            " ".join(recipe.elements),
            " ".join(recipe.pre),
            " ".join(recipe.sol),
            " ".join(recipe.outputs),
            " ".join(recipe.checks),
            " ".join(recipe.pitfalls),
        ]
        hay = " ".join(hay_parts).lower()
        if words and not all(w in hay for w in words):
            continue
        score = sum(hay.count(w) for w in words) if words else 1
        score += 4 if any(w in recipe.name.lower() for w in words) else 0
        score += 2 if any(w in " ".join(recipe.tags).lower() for w in words) else 0
        scored.append((score, recipe))
    scored.sort(key=lambda item: (-item[0], item[1].name))
    return scored[: max(1, min(top_k, 20))]


def format_recipe_index(recipes: list[ElfRecipe]) -> str:
    if not recipes:
        return "No recipes match the requested filters."
    lines = [f"# ELF workflow recipes ({len(recipes)} recipes)", ""]
    for recipe in recipes:
        lines.append(
            f"- `{recipe.name}` ({recipe.solver}): {recipe.title} "
            f"[tags: {', '.join(recipe.tags)}]"
        )
    return "\n".join(lines)


def format_recipe(recipe: ElfRecipe) -> str:
    def bullet(label: str, values: tuple[str, ...]) -> list[str]:
        lines = [f"## {label}"]
        lines.extend(f"- {value}" for value in values)
        return lines

    lines = [
        f"# {recipe.name}: {recipe.title}",
        "",
        f"- solver: {recipe.solver}",
        f"- goal: {recipe.goal}",
        f"- tags: {', '.join(recipe.tags)}",
        "",
    ]
    lines.extend(bullet("Use When", recipe.use_when))
    lines.extend([""])
    lines.extend(bullet("Elements", recipe.elements))
    lines.extend([""])
    lines.extend(bullet("PRE", recipe.pre))
    lines.extend([""])
    lines.extend(bullet("SOL", recipe.sol))
    lines.extend([""])
    lines.extend(bullet("Outputs", recipe.outputs))
    lines.extend([""])
    lines.extend(bullet("Checks", recipe.checks))
    lines.extend([""])
    lines.extend(bullet("Pitfalls", recipe.pitfalls))
    lines.extend([""])
    lines.extend(bullet("Examples", recipe.examples))
    lines.extend([""])
    lines.extend(bullet("Next Recipes", recipe.next_steps))
    return "\n".join(lines).rstrip()


def format_search_results(results: list[tuple[int, ElfRecipe]], query: str) -> str:
    if not results:
        return f"No recipes match '{query}'. Try elf_recipe_index() to browse all recipes."
    lines = [f"# {len(results)} recipe matches for '{query}'", ""]
    for score, recipe in results:
        lines.append(f"## {recipe.name}  (score={score})")
        lines.append(f"- title: {recipe.title}")
        lines.append(f"- goal: {recipe.goal}")
        lines.append(f"- tags: {', '.join(recipe.tags)}")
        lines.append(f"- next: elf_recipe_get(\"{recipe.name}\")")
        lines.append("")
    return "\n".join(lines).rstrip()


def plan_workflow(goal: str) -> str:
    """Return a short workflow plan for a natural-language goal."""
    matches = search_recipes(goal, top_k=4)
    if not matches:
        return "No matching workflow recipe. Try elf_recipe_index() and choose a closer tag."

    primary = matches[0][1]
    ordered = [primary]
    for next_name in primary.next_steps:
        next_recipe = get_recipe(next_name)
        if next_recipe and next_recipe not in ordered:
            ordered.append(next_recipe)
        if len(ordered) >= 4:
            break
    for _score, recipe in matches[1:]:
        if recipe not in ordered:
            ordered.append(recipe)
        if len(ordered) >= 4:
            break

    lines = [
        f"# ELF workflow plan for: {goal}",
        "",
        f"Primary recipe: `{primary.name}` - {primary.title}",
        "",
        "## Suggested Sequence",
    ]
    for i, recipe in enumerate(ordered, 1):
        lines.append(f"{i}. `{recipe.name}` - {recipe.goal}")
    lines.extend(
        [
            "",
            "## First Checks",
            *[f"- {check}" for check in primary.checks],
            "",
            "## Common Pitfalls",
            *[f"- {pitfall}" for pitfall in primary.pitfalls],
            "",
            f"Drill down with: elf_recipe_get(\"{primary.name}\")",
        ]
    )
    return "\n".join(lines)
