#!/usr/bin/env python3
"""
Climate data analysis with xarray.

Usage:
    python climate_analysis.py <netcdf_file> [--var VARIABLE] [--output OUTPUT_DIR]
    python climate_analysis.py data.nc --var temperature --output results/
"""

import argparse
from pathlib import Path

import numpy as np
import xarray as xr


def compute_climatology(ds: xr.Dataset, var: str) -> xr.Dataset:
    """
    Compute monthly climatology for a variable.

    Args:
        ds: Input dataset
        var: Variable name

    Returns:
        Dataset with monthly climatology
    """
    climatology = ds[var].groupby("time.month").mean("time")
    return climatology.to_dataset(name=f"{var}_climatology")


def compute_anomalies(ds: xr.Dataset, var: str) -> xr.Dataset:
    """
    Compute anomalies from monthly climatology.

    Args:
        ds: Input dataset
        var: Variable name

    Returns:
        Dataset with anomalies
    """
    climatology = ds[var].groupby("time.month").mean("time")
    anomalies = ds[var].groupby("time.month") - climatology
    return anomalies.to_dataset(name=f"{var}_anomaly")


def compute_trends(ds: xr.Dataset, var: str) -> xr.Dataset:
    """
    Compute linear trend per grid cell.

    Args:
        ds: Input dataset
        var: Variable name

    Returns:
        Dataset with trend (per year) and p-values
    """
    from scipy import stats

    data = ds[var]

    # Convert time to years
    time_years = (data.time - data.time[0]).dt.days / 365.25

    def linear_trend(y):
        """Compute linear trend slope."""
        mask = ~np.isnan(y)
        if mask.sum() < 3:
            return np.nan
        x = time_years.values[mask]
        y_clean = y[mask]
        slope, _, _, _, _ = stats.linregress(x, y_clean)
        return slope

    # Apply along time dimension
    trend = xr.apply_ufunc(
        linear_trend,
        data,
        input_core_dims=[["time"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )

    result = xr.Dataset()
    result[f"{var}_trend"] = trend
    result[f"{var}_trend"].attrs["units"] = f"{data.attrs.get('units', 'units')}/year"
    result[f"{var}_trend"].attrs["long_name"] = f"Linear trend of {var}"

    return result


def compute_spatial_statistics(ds: xr.Dataset, var: str) -> dict:
    """
    Compute area-weighted spatial statistics.

    Args:
        ds: Input dataset
        var: Variable name

    Returns:
        Dictionary with statistics
    """
    data = ds[var]

    # Area weights (cosine of latitude)
    if "lat" in ds.coords:
        weights = np.cos(np.deg2rad(ds.lat))
        weighted_mean = data.weighted(weights).mean(dim=["lat", "lon"])
    else:
        weighted_mean = data.mean(dim=list(data.dims[1:]))  # All spatial dims

    stats = {
        "global_mean": float(data.mean().values),
        "global_std": float(data.std().values),
        "global_min": float(data.min().values),
        "global_max": float(data.max().values),
    }

    if "time" in data.dims:
        stats["time_series_mean"] = float(weighted_mean.mean().values)
        stats["time_series_std"] = float(weighted_mean.std().values)

    return stats


def compute_seasonal_cycle(ds: xr.Dataset, var: str) -> xr.Dataset:
    """
    Compute seasonal cycle (monthly means).

    Args:
        ds: Input dataset
        var: Variable name

    Returns:
        Dataset with 12 monthly values
    """
    data = ds[var]

    # Area-weighted mean if spatial dimensions exist
    if "lat" in ds.coords:
        weights = np.cos(np.deg2rad(ds.lat))
        spatial_mean = data.weighted(weights).mean(dim=["lat", "lon"])
    else:
        spatial_mean = data.mean(dim=list(data.dims[1:]))

    # Monthly mean
    seasonal_cycle = spatial_mean.groupby("time.month").mean()

    return seasonal_cycle.to_dataset(name=f"{var}_seasonal_cycle")


def analyze_climate_file(filepath: str, var: str = None, output_dir: str = None) -> dict:
    """
    Run full climate analysis on a NetCDF file.

    Args:
        filepath: Path to NetCDF file
        var: Variable to analyze (auto-detect if None)
        output_dir: Directory to save results (optional)

    Returns:
        Dictionary with analysis results
    """
    # Open dataset
    ds = xr.open_dataset(filepath)

    # Auto-detect variable if not specified
    if var is None:
        # Skip coordinate-like variables
        data_vars = [v for v in ds.data_vars if len(ds[v].dims) >= 2]
        if not data_vars:
            raise ValueError("No suitable data variables found")
        var = data_vars[0]
        print(f"Auto-selected variable: {var}")

    if var not in ds.data_vars:
        raise ValueError(f"Variable '{var}' not found. Available: {list(ds.data_vars)}")

    results = {"variable": var, "filepath": str(filepath)}

    # Dataset info
    results["info"] = {
        "dims": dict(ds.dims),
        "time_range": None,
        "lat_range": None,
        "lon_range": None,
    }

    if "time" in ds.coords:
        results["info"]["time_range"] = [
            str(ds.time.values[0]),
            str(ds.time.values[-1]),
        ]
    if "lat" in ds.coords:
        results["info"]["lat_range"] = [float(ds.lat.min()), float(ds.lat.max())]
    if "lon" in ds.coords:
        results["info"]["lon_range"] = [float(ds.lon.min()), float(ds.lon.max())]

    # Compute statistics
    print("Computing spatial statistics...")
    results["statistics"] = compute_spatial_statistics(ds, var)

    # Save outputs if requested
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print("Computing climatology...")
        climatology = compute_climatology(ds, var)
        climatology.to_netcdf(output_path / f"{var}_climatology.nc")

        print("Computing anomalies...")
        anomalies = compute_anomalies(ds, var)
        anomalies.to_netcdf(output_path / f"{var}_anomalies.nc")

        print("Computing seasonal cycle...")
        seasonal = compute_seasonal_cycle(ds, var)
        seasonal.to_netcdf(output_path / f"{var}_seasonal_cycle.nc")

        print(f"Results saved to {output_path}")

    ds.close()
    return results


def print_results(results: dict) -> None:
    """Print analysis results."""
    print("\n" + "=" * 60)
    print(f"Climate Analysis Results")
    print("=" * 60)

    print(f"\nFile: {results['filepath']}")
    print(f"Variable: {results['variable']}")

    print("\nDataset Info:")
    info = results["info"]
    print(f"  Dimensions: {info['dims']}")
    if info["time_range"]:
        print(f"  Time range: {info['time_range'][0]} to {info['time_range'][1]}")
    if info["lat_range"]:
        print(f"  Latitude range: {info['lat_range'][0]:.2f} to {info['lat_range'][1]:.2f}")
    if info["lon_range"]:
        print(f"  Longitude range: {info['lon_range'][0]:.2f} to {info['lon_range'][1]:.2f}")

    print("\nStatistics:")
    stats = results["statistics"]
    print(f"  Global mean: {stats['global_mean']:.4f}")
    print(f"  Global std:  {stats['global_std']:.4f}")
    print(f"  Global min:  {stats['global_min']:.4f}")
    print(f"  Global max:  {stats['global_max']:.4f}")

    if "time_series_mean" in stats:
        print(f"\n  Area-weighted time series mean: {stats['time_series_mean']:.4f}")
        print(f"  Area-weighted time series std:  {stats['time_series_std']:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Climate data analysis with xarray",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python climate_analysis.py temperature.nc
    python climate_analysis.py climate.nc --var tas
    python climate_analysis.py climate.nc --var tas --output results/
        """,
    )
    parser.add_argument("file", help="NetCDF file to analyze")
    parser.add_argument("--var", help="Variable name (auto-detect if not specified)")
    parser.add_argument("--output", help="Output directory for results")
    args = parser.parse_args()

    results = analyze_climate_file(args.file, args.var, args.output)
    print_results(results)


if __name__ == "__main__":
    main()
