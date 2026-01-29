#!/usr/bin/env python3
"""
DC Resistivity Inversion Example.

Demonstrates a complete DC resistivity inversion workflow:
1. Create mesh
2. Define survey geometry
3. Generate synthetic data
4. Run inversion
5. Plot results

Usage:
    python dc_inversion.py
    python dc_inversion.py --n-electrodes 41 --spacing 5
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from discretize import TensorMesh

from simpeg import data, data_misfit, directives, inverse_problem, inversion
from simpeg import maps, optimization, regularization
from simpeg.electromagnetics.static import resistivity as dc


def create_mesh(survey_length: float, electrode_spacing: float) -> TensorMesh:
    """
    Create 2D tensor mesh for DC resistivity.

    Parameters
    ----------
    survey_length : float
        Total length of survey line in meters
    electrode_spacing : float
        Spacing between electrodes in meters

    Returns
    -------
    TensorMesh
        2D mesh with padding
    """
    # Core cell size based on electrode spacing
    cell_size = electrode_spacing / 2

    # Core region covers survey + buffer
    n_core_x = int(survey_length / cell_size) + 20
    n_core_z = int(survey_length / 2 / cell_size)

    # Create cells with padding
    hx_core = np.ones(n_core_x) * cell_size
    hx_pad = cell_size * 1.3 ** np.arange(1, 12)
    hx = np.hstack([hx_pad[::-1], hx_core, hx_pad])

    hz_core = np.ones(n_core_z) * cell_size
    hz_pad = cell_size * 1.3 ** np.arange(1, 10)
    hz = np.hstack([hz_core, hz_pad])

    mesh = TensorMesh([hx, hz], origin="CN")

    print(f"Mesh created: {mesh.nC} cells")
    print(f"  x range: [{mesh.nodes_x.min():.1f}, {mesh.nodes_x.max():.1f}] m")
    print(f"  z range: [{mesh.nodes_x.min():.1f}, {mesh.nodes_x.max():.1f}] m")

    return mesh


def create_dipole_dipole_survey(
    n_electrodes: int, electrode_spacing: float
) -> dc.Survey:
    """
    Create dipole-dipole DC resistivity survey.

    Parameters
    ----------
    n_electrodes : int
        Number of electrodes along survey line
    electrode_spacing : float
        Spacing between electrodes in meters

    Returns
    -------
    dc.Survey
        Survey object with dipole-dipole configuration
    """
    # Electrode locations centered at x=0
    survey_length = (n_electrodes - 1) * electrode_spacing
    electrode_x = np.linspace(-survey_length / 2, survey_length / 2, n_electrodes)
    electrode_locs = np.c_[electrode_x, np.zeros(n_electrodes)]

    source_list = []
    for i in range(n_electrodes - 3):
        # Current electrodes
        a_loc = electrode_locs[i]
        b_loc = electrode_locs[i + 1]

        # Potential electrodes for multiple n-spacings
        rx_list = []
        for n in range(1, min(8, n_electrodes - i - 2)):
            m_loc = electrode_locs[i + 1 + n]
            n_loc = electrode_locs[i + 2 + n]
            rx = dc.receivers.Dipole(m_loc.reshape(1, -1), n_loc.reshape(1, -1))
            rx_list.append(rx)

        if rx_list:
            src = dc.sources.Dipole(rx_list, a_loc, b_loc)
            source_list.append(src)

    survey = dc.Survey(source_list)
    print(f"Survey created: {survey.nD} data points from {len(source_list)} sources")

    return survey


def create_true_model(mesh: TensorMesh) -> np.ndarray:
    """
    Create synthetic resistivity model with anomalies.

    Parameters
    ----------
    mesh : TensorMesh
        Mesh for model

    Returns
    -------
    np.ndarray
        Resistivity model (ohm-m)
    """
    # Background resistivity
    model = np.ones(mesh.nC) * 100.0  # 100 ohm-m

    # Conductive anomaly (left side)
    inds_cond = (
        (mesh.cell_centers[:, 0] > -60)
        & (mesh.cell_centers[:, 0] < -20)
        & (mesh.cell_centers[:, 1] > -40)
        & (mesh.cell_centers[:, 1] < -10)
    )
    model[inds_cond] = 10.0  # 10 ohm-m

    # Resistive anomaly (right side)
    inds_res = (
        (mesh.cell_centers[:, 0] > 20)
        & (mesh.cell_centers[:, 0] < 60)
        & (mesh.cell_centers[:, 1] > -50)
        & (mesh.cell_centers[:, 1] < -15)
    )
    model[inds_res] = 1000.0  # 1000 ohm-m

    print(f"True model: {model.min():.1f} - {model.max():.1f} ohm-m")

    return model


def run_forward(
    mesh: TensorMesh, survey: dc.Survey, model: np.ndarray, noise_pct: float = 0.05
) -> data.Data:
    """
    Run forward model and add noise.

    Parameters
    ----------
    mesh : TensorMesh
        Mesh for simulation
    survey : dc.Survey
        Survey geometry
    model : np.ndarray
        Resistivity model (ohm-m)
    noise_pct : float
        Noise level as fraction of data magnitude

    Returns
    -------
    data.Data
        Synthetic observed data with noise
    """
    # Map: model is log(conductivity), output is conductivity
    sigma_map = maps.ExpMap(mesh)

    # Simulation
    simulation = dc.Simulation2DNodal(mesh, survey=survey, sigmaMap=sigma_map)

    # Forward model (input: log conductivity)
    log_sigma = np.log(1.0 / model)
    dpred = simulation.dpred(log_sigma)

    # Add noise
    noise = noise_pct * np.abs(dpred) * np.random.randn(len(dpred))
    dobs = dpred + noise

    # Standard deviation
    std = noise_pct * np.abs(dobs) + 1e-10 * np.abs(dobs).max()

    obs_data = data.Data(survey, dobs=dobs, standard_deviation=std)
    print(f"Forward model complete: {len(dobs)} data points")

    return obs_data


def run_inversion(
    mesh: TensorMesh,
    survey: dc.Survey,
    obs_data: data.Data,
    max_iter: int = 20,
) -> np.ndarray:
    """
    Run DC resistivity inversion.

    Parameters
    ----------
    mesh : TensorMesh
        Mesh for inversion
    survey : dc.Survey
        Survey geometry
    obs_data : data.Data
        Observed data
    max_iter : int
        Maximum iterations

    Returns
    -------
    np.ndarray
        Recovered resistivity model (ohm-m)
    """
    # Mapping
    sigma_map = maps.ExpMap(mesh)

    # Simulation
    simulation = dc.Simulation2DNodal(mesh, survey=survey, sigmaMap=sigma_map)

    # Data misfit
    dmis = data_misfit.L2DataMisfit(data=obs_data, simulation=simulation)

    # Regularization
    reg = regularization.WeightedLeastSquares(
        mesh, alpha_s=1e-2, alpha_x=1.0, alpha_y=1.0
    )

    # Optimization
    opt = optimization.InexactGaussNewton(maxIter=max_iter, maxIterCG=20)
    opt.remember("xc")

    # Inverse problem
    inv_prob = inverse_problem.BaseInvProblem(dmis, reg, opt)

    # Directives
    starting_beta = directives.BetaEstimate_ByEig(beta0_ratio=1e1)
    beta_schedule = directives.BetaSchedule(coolingFactor=2, coolingRate=1)
    target_misfit = directives.TargetMisfit(chifact=1.0)
    save_iteration = directives.SaveOutputEveryIteration()

    dir_list = [starting_beta, beta_schedule, target_misfit, save_iteration]

    # Inversion
    inv = inversion.BaseInversion(inv_prob, directiveList=dir_list)

    # Starting model (homogeneous 100 ohm-m)
    m0 = np.log(1.0 / 100.0) * np.ones(mesh.nC)

    print("Running inversion...")
    mrec = inv.run(m0)

    # Convert to resistivity
    sigma_rec = sigma_map * mrec
    rho_rec = 1.0 / sigma_rec

    print(f"Inversion complete: {rho_rec.min():.1f} - {rho_rec.max():.1f} ohm-m")

    return rho_rec


def plot_results(
    mesh: TensorMesh,
    true_model: np.ndarray,
    recovered_model: np.ndarray,
    output_file: str = None,
) -> None:
    """
    Plot true and recovered models.

    Parameters
    ----------
    mesh : TensorMesh
        Mesh for plotting
    true_model : np.ndarray
        True resistivity model
    recovered_model : np.ndarray
        Recovered resistivity model
    output_file : str, optional
        Path to save figure
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Plot limits
    vmin, vmax = 10, 1000
    depth_max = 100

    # True model
    ax = axes[0]
    mesh.plot_image(
        np.log10(true_model),
        ax=ax,
        grid=False,
        clim=[np.log10(vmin), np.log10(vmax)],
        pcolor_opts={"cmap": "viridis"},
    )
    ax.set_xlim([-150, 150])
    ax.set_ylim([-depth_max, 10])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.set_title("True Resistivity Model")
    ax.set_aspect("equal")

    # Recovered model
    ax = axes[1]
    im = mesh.plot_image(
        np.log10(recovered_model),
        ax=ax,
        grid=False,
        clim=[np.log10(vmin), np.log10(vmax)],
        pcolor_opts={"cmap": "viridis"},
    )
    ax.set_xlim([-150, 150])
    ax.set_ylim([-depth_max, 10])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("z (m)")
    ax.set_title("Recovered Resistivity Model")
    ax.set_aspect("equal")

    # Colorbar
    cbar = plt.colorbar(im[0], ax=axes, shrink=0.6, label="log10(Resistivity) [ohm-m]")

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"Figure saved: {output_file}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="DC Resistivity Inversion Example")
    parser.add_argument(
        "--n-electrodes", type=int, default=21, help="Number of electrodes"
    )
    parser.add_argument(
        "--spacing", type=float, default=10.0, help="Electrode spacing (m)"
    )
    parser.add_argument(
        "--max-iter", type=int, default=15, help="Maximum inversion iterations"
    )
    parser.add_argument("--output", type=str, default=None, help="Output figure path")
    parser.add_argument(
        "--noise", type=float, default=0.05, help="Noise level (fraction)"
    )
    args = parser.parse_args()

    # Survey parameters
    survey_length = (args.n_electrodes - 1) * args.spacing

    # Create mesh
    mesh = create_mesh(survey_length, args.spacing)

    # Create survey
    survey = create_dipole_dipole_survey(args.n_electrodes, args.spacing)

    # Create true model
    true_model = create_true_model(mesh)

    # Forward model
    obs_data = run_forward(mesh, survey, true_model, noise_pct=args.noise)

    # Inversion
    recovered_model = run_inversion(mesh, survey, obs_data, max_iter=args.max_iter)

    # Plot
    plot_results(mesh, true_model, recovered_model, output_file=args.output)


if __name__ == "__main__":
    main()
