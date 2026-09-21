# DA401 Capstone Project - Viet Nguyen

## Project Title

AI or Overhiring? Explaining the Post-Pandemic Decline in Early-Career Hiring

## Research Question

After accounting for unusually high pandemic-era employment growth, is greater exposure to generative AI related to lower hiring among workers ages 22 to 24?

The project will consider both AI-related labor restructuring and a post-pandemic return toward normal employment levels, without assuming either explanation is correct.

## Planned Data Sources

- [U.S. Census Bureau&#39;s Quarterly Workforce Indicators (QWI)](https://qwiexplorer.ces.census.gov/): hiring, employment, and separations by state, industry, age group, and quarter. Four-digit NAICS industries will be used if coverage permits.
- Occupational AI exposure measures from Eloundou et al. (2024), aggregated to industries using pre-pandemic occupation-industry employment shares.

## Planned Methods

Using Python, the analysis will estimate how far actual 2022 employment in each state-industry group was above or below its pre-COVID trend. Descriptive visualizations and difference-in-differences panel regressions will then compare hiring changes before and after ChatGPT's introduction, accounting for AI exposure and pandemic employment growth.

The main model will include state-industry and quarter fixed effects, with standard errors clustered by industry. An event study will examine pre-existing trends; comparisons with older workers and alternative employment forecasts may be added if feasible.

## Tentative Timeline

- **September to early October:** Refine the literature review, research design, and variables.
- **October:** Collect and clean data, estimate initial models, and present early results.
- **November:** Complete the main analysis, draft the paper, and incorporate feedback.
- **December:** Finalize the paper, document the code, and prepare the executive summary and poster.

## Repository Structure

- `docs/`: Initial proposal and supporting documents
- `code/`: All analysis scripts or notebooks
- `writing/`: Proposal, drafts, final paper
- `figures/`: Plots, charts, visualizations
- `data/`: Only small sample data (large files go in Google Drive)
