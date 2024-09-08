
# Connectographics: A Graphical User Interface for Visualizing Human Connectomes
# Overview
Connectographics is a user-friendly graphical interface designed to aid researchers and clinicians in visualizing human connectomes. This tool helps users interactively generate connectogram visualizations from neuroimaging data, providing easy access to connectome analyses without requiring advanced programming skills.

This Python-based tool integrates with Circos to produce visual representations of brain connections. Users can select or create subject folders, generate link files from connectivity matrices, create heatmaps, and run Circos to visualize connectograms. It also provides an interactive interface for uploading files and visualizing the results within the GUI.

# Features
Link File Generation: Convert brain region matrices into a link file with connection strengths.
Heatmap Generation: Generate heatmaps and configuration files based on specific metrics (e.g., brain structure metrics).
Circos Integration: Easily run Circos to generate connectograms directly from the GUI.
Graphical Interface: User-friendly interface to handle all operations without command-line interaction.
Prerequisites
To run this application, you will need the following software installed on your machine:

# Python 3.x
Circos (for generating connectograms)
Freesurfer (optional for reading specific brain data)
