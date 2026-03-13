[README.md](https://github.com/user-attachments/files/25956109/README.md)
# Sentiment WordCloud Generator for Education and Research

A Streamlit-based data visualization tool designed to analyze and summarize open-ended survey responses and feedback in educational and scientific settings.

## Overview
This application supports researchers and educators by transforming qualitative text data from Excel or CSV files into intuitive WordClouds. It is specifically optimized for Japanese morphological analysis, enabling users to quickly grasp key themes and sentiments from large datasets.

The app is designed to bridge the gap between raw data collection and actionable qualitative insights.

## Key Features
- **File Support**: Directly upload .xlsx or .csv files.
- **Japanese Text Analysis**: Utilizes Janome for high-precision tokenization and part-of-speech tagging.
- **Smart Filtering**: 
  - Automatically extracts nouns and filters out common stop-words and functional words.
  - Allows users to select specific columns for analysis from the uploaded dataset.
- **Visual Feedback**: Generates high-resolution WordClouds with customizable parameters.
- **Export Option**: Download the generated visualization as a PNG file for inclusion in reports or presentations.

## Design Philosophy
This tool was developed to meet professional and academic needs:
- **Efficiency**: Significantly reduces the time required to review large volumes of descriptive text.
- **Research Support**: Assists in qualitative data analysis for biological and ecological studies.
- **Objective Visualization**: Provides a data-driven overview of participant feedback to support evidence-based decision-making.

## Technologies Used
- **Language**: Python
- **Web Framework**: Streamlit
- **Morphological Analysis**: Janome
- **Data Processing**: Pandas
- **Visualization**: WordCloud, Matplotlib
- **Infrastructure**: GitHub, Streamlit Cloud

## Security and Data Privacy
- **In-Memory Processing**: This application processes data in-memory. Uploaded files are not stored on the server or the GitHub repository.
- **Data Handling**: To ensure compliance with data protection standards, it is recommended to remove personally identifiable information (PII) before uploading datasets to the application.

## Author
Developed by a researcher and educator specializing in Science Education and Data Science.
