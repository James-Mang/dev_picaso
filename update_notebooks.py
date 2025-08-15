import json
import os
import sys

notebooks = [
    "docs/notebooks/References.ipynb",
    "docs/notebooks/F_fitdata/WIP_5_GridRetrieval_CreatingTemplates.ipynb",
    "docs/notebooks/F_fitdata/WIP_4_GridRetrieval_GridFittingWithClouds.ipynb",
    "docs/notebooks/F_fitdata/WIP_2_GridRetrieval.ipynb",
    "docs/notebooks/F_fitdata/1_GridSearch.ipynb",
    "docs/notebooks/F_fitdata/WIP_3_GridRetrieval_GridFitting.ipynb",
    "docs/notebooks/B_chemistry/1_ChemicalEquilibrium.ipynb",
    "docs/notebooks/B_chemistry/2_Photochemistry.ipynb",
    "docs/notebooks/I_usefultools/CommonClimateBDIssues.ipynb",
    "docs/notebooks/I_usefultools/Sqlite3Tutorial.ipynb",
    "docs/notebooks/I_usefultools/FAQs.ipynb",
    "docs/notebooks/I_usefultools/Level_Fluxes.ipynb",
    "docs/notebooks/I_usefultools/data_uniformity_tutorial.ipynb",
    "docs/notebooks/I_usefultools/ModelStorage.ipynb",
    "docs/notebooks/I_usefultools/ContributionFunctions.ipynb",
    "docs/notebooks/workshops/SaganSchool2023/HowToAnalyzeExoplanetSpectra.ipynb",
    "docs/notebooks/workshops/SaganSchool2021/3_Chemistry.ipynb",
    "docs/notebooks/workshops/SaganSchool2021/2_HotVsCold.ipynb",
    "docs/notebooks/workshops/SaganSchool2021/4_Clouds.ipynb",
    "docs/notebooks/workshops/SaganSchool2021/1_Spectroscopy.ipynb",
    "docs/notebooks/workshops/ERS2021/ThermalEmissionTutorial.ipynb",
    "docs/notebooks/workshops/SaganSchool2020/JWSTProposalTutorial.ipynb",
    "docs/notebooks/workshops/ESO2021/ESO_Tutorial.ipynb",
    "docs/notebooks/C_clouds/1_PairingPICASOToVIRGA.ipynb",
    "docs/notebooks/C_clouds/2_PatchyClouds.ipynb",
    "docs/notebooks/G_opacities/2_CreatingOpacityDb.ipynb",
    "docs/notebooks/G_opacities/1_QueryOpacities.ipynb",
    "docs/notebooks/G_opacities/4_CorrelatedKTables.ipynb",
    "docs/notebooks/G_opacities/3_ResamplingOpacities.ipynb",
    "docs/notebooks/H_radiativetransfer/1_AnalyzingApproximationsReflectedLightToon.ipynb",
    "docs/notebooks/H_radiativetransfer/2_AnalyzingApproximationsReflectedLightSH.ipynb",
    "docs/notebooks/H_radiativetransfer/3_AnalyzingApproximationsThermal.ipynb",
    "docs/notebooks/D_climate/7_CreateModelGrid.ipynb",
    "docs/notebooks/D_climate/3_Exoplanet-Photochemistry.ipynb",
    "docs/notebooks/D_climate/4b_BrownDwarf_DEQ_const_kzz.ipynb",
    "docs/notebooks/D_climate/6_CloudyBrownDwarf_DEQ.ipynb",
    "docs/notebooks/D_climate/1b_BrownDwarf_ResortRebin_Chemeq.ipynb",
    "docs/notebooks/D_climate/5_CloudyBrownDwarf_PreW.ipynb",
    "docs/notebooks/D_climate/8_EnergyInjection.ipynb",
    "docs/notebooks/D_climate/1_BrownDwarf_PreW.ipynb",
    "docs/notebooks/D_climate/2b_Exoplanet-ResortRebin-Chemeq.ipynb",
    "docs/notebooks/D_climate/2_Exoplanet_PreW.ipynb",
    "docs/notebooks/D_climate/4_BrownDwarf_DEQ_SC_kzz.ipynb",
    "docs/notebooks/D_climate/9_BrownDwarf_Moistgrad.ipynb",
    "docs/notebooks/Quickstart.ipynb",
    "docs/notebooks/J_driver_WIP/driver.ipynb",
    "docs/notebooks/J_driver_WIP/WIP_Parameterizations.ipynb",
    "docs/notebooks/A_basics/5_AddingThermalFlux.ipynb",
    "docs/notebooks/A_basics/4_PlotDiagnostics.ipynb",
    "docs/notebooks/A_basics/2_AddingClouds.ipynb",
    "docs/notebooks/A_basics/3_AddingSurfaceReflectivity.ipynb",
    "docs/notebooks/A_basics/6_AddingTransitSpectrum.ipynb",
    "docs/notebooks/A_basics/7_BrownDwarfs.ipynb",
    "docs/notebooks/A_basics/1_GetStarted.ipynb",
    "docs/notebooks/E_3dmodeling/5_3DSpectra.ipynb",
    "docs/notebooks/E_3dmodeling/3_PostProcess3Dinput-Chemistry.ipynb",
    "docs/notebooks/E_3dmodeling/2_3DInputsWithPICASOandXarray.ipynb",
    "docs/notebooks/E_3dmodeling/1_SphericalIntegration.ipynb",
    "docs/notebooks/E_3dmodeling/7_PhaseCurves-wChemEq.ipynb",
    "docs/notebooks/E_3dmodeling/6_PhaseCurves.ipynb",
    "docs/notebooks/E_3dmodeling/8_ReflectedPhaseCurve.ipynb",
    "docs/notebooks/E_3dmodeling/4_PostProcess3Dinput-Clouds.ipynb"
]

new_source = [
    "import picaso.data as d\n",
    "\n",
    "#pick a path to download all the reference data\n",
    "d.os.environ['picaso_refdata'] = '/data/reference_data/picaso/reftest'\n",
    "\n",
    "#get all needed data\n",
    "d.get_data(category_download='picaso-lite', target_download='tutorial_sagan23',final_destination_dir=d.os.environ['picaso_refdata'] )\n",
    "\n",
    "#add this to the top of any picaso notebook that models exoplanets\n",
    "d.os.environ['PYSYN_CDBS'] = d.os.path.join(d.os.environ['picaso_refdata'],'stellar_grids')\n",
    "\n",
    "mieff_dir = d.os.path.join(d.os.environ['picaso_refdata'],'virga')\n",
    "ck_dir = d.os.path.join(d.os.environ['picaso_refdata'],'opacities', 'preweighted')"
]

if len(sys.argv) != 2:
    print("Usage: python update_notebooks.py <index>")
    sys.exit(1)

index = int(sys.argv[1])

notebook_path = notebooks[index]
try:
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)

    # Find the first code cell and replace its source
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            cell['source'] = new_source
            break

    with open(notebook_path, 'w') as f:
        json.dump(notebook, f, indent=1)
    print(f"Updated {notebook_path}")
except Exception as e:
    print(f"Error updating {notebook_path}: {e}")
