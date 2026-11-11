# Macalester DS 456 - Projects in Data Science - Codex Activity
## Names: Karyna & Yeshe


*Originally created by Shilad Sen (with help from Codex), 2025/11/25. Updated by Bret Jackson 2026/11/08*

In this activity you will:

- Use Codex as a collaborator on a real spatial dataset.
- Practice being *critical* of Codex’s suggestions (not just accepting them).
- Progress from exploration to a reviewed analysis plan, implement it with Codex, and verify one important result.

# 0. Get the project

- Fork the [Codex Activity](https://github.com/bretjackson/ds-456-codex-activity) on GitHub.
- Clone **your fork** (not the original) to your computer.

# 1. Choose your tools and set up Codex

You may work in **Python (VS Code)** or **R (VS Code or RStudio)**.

## 1.1 Highly Recommended: VS Code + Codex (Python or R)

- Install [VS Code](https://code.visualstudio.com/).
- Install the [Codex VS Code extension](https://developers.openai.com/codex/ide/).
- If you are using R, also install the [VS Code R extension](https://marketplace.visualstudio.com/items?itemName=reditorsupport.r).
- Open your cloned repo folder in VS Code.
- In the Codex sidebar:
  - Click “Use API Key” and use the key Shilad gave you.  
    **DO NOT PUT THIS KEY ANYWHERE IN YOUR GITHUB REPO.**
  - Open Codex settings → “Open `config.toml`” and set it to:
    ```toml
    model = "gpt-6.1-sol"
    model_reasoning_effort = "medium"
    web_search = "live"

    [sandbox_workspace_write]
    network_access = true
    ```
  - Restart VS Code after editing `config.toml`.

## 1.2 Optional: RStudio + Codex in a separate terminal

If you strongly prefer RStudio:

- Use **RStudio** for your R scripts / Rmd files.
- Using a terminal, install the Codex CLI: `npm i -g @openai/codex`
- In a terminal, run `codex` once so it creates a config file at `~/.codex/config.toml`.
- Open `~/.codex/config.toml` in any text editor you like (VS Code, TextEdit, Notepad, `nano`, etc.) and paste the same settings shown in 1.1.
- In a separate terminal window (**from the repo root**), run Codex and use it to:
  - Draft and refactor R code.
  - Ask questions about errors.
- You are still responsible for keeping all code and writeups in this repo so they can be graded.

# 2. Create your assignment skeleton

You will **not** edit this `README.md` directly. Instead:

- Copy `README.md` to `Codex_Activity.md`.
- Add your name(s) at the top of `Codex_Activity.md`.
- For every prompt marked **Task:** below, you will write your answers in `Codex_Activity.md`.
- Your actual analysis code should live in code files, for example:
  - R: `analysis/codex_activity.qmd` or `analysis/codex_activity.R`
  - Python: `analysis/codex_activity.ipynb` or `analysis/codex_activity.py`

You may reference your code files from `Codex_Activity.md` (e.g., “see Figure 1 in `analysis/codex_activity.Rmd`”).

Keep using the same Codex conversation as you move from exploration to mapping and analysis, including when you return for the second class session. If you start a new conversation, provide your research question (if chosen), relevant file paths, and a short summary of what you have discovered.

# 3. Early dataset interactions

- Pick a spatial dataset from [Open Data Minneapolis](https://opendata.minneapolismn.gov).  
  One fun option (used in the instructor example) is  
  [Motorized Foot & eBike Trips in 2025](https://opendata.minneapolismn.gov/datasets/d9a1f322528447ff9c1bc86e5d0895c5_0/explore).
- Give Codex the URL for the dataset and ask it to help you get started understanding the data.  
  Keep your request intentionally vague (e.g., “Help me explore this dataset”).

**Task 3.1 (in `Codex_Activity.md`):**  
In 2–3 short bullets, describe what you notice about this early interaction. Consider:

- What did Codex assume or gloss over?
- Did it make any mistakes or questionable choices?
- How clear or explainable was the code it produced?
  * Codex assumed the most useful fields we would like to start with
  * No mistakes of note; reported its findings
  * No code was produced but explanation was clear

Retain useful code and observations from this interaction so you can build on them in the next sections.

# 4. More directed exploration

- If you are partner coding, *switch partners*.
- Download the dataset you would like to analyze and move it under `data/`.
- Ask Codex to help you analyze the **basic information** about the dataset:
  - basic summaries (rows, columns, variable types),
  - simple visualizations,
  - any surprising patterns.
- Then ask Codex for specific improvements (e.g., “Use `dplyr` instead of base R”, “Add labels and titles”, “Handle missing values more carefully”).
- Save useful exploration code in your analysis file and keep notes about relevant variables and assumptions. You will reuse this work for mapping and your research question.

**Task 4.1 (in `Codex_Activity.md`):**
Respond in 2–3 short bullets, considering:

- What did Codex do well?
- What would you have done differently if you wrote the code yourself?
- Looking at the code Codex wrote, what could be improved (style, clarity, correctness, efficiency)?

  * It generated plots that summarized data and did provide some surface level insight
  * It created an MD and requirements file that held all of the notes on what it did
  * In one of the plots, one of the values was redundant and included as a quality check, but we would not have included it as it was unecessary and caused clutter on the plot

# 5. Mapping the data

- If you are partner coding, *switch partners*.
- Discuss with your partner how you could geocode / map the data.
- Once you have an idea for how to do it, ask Codex to help you map your data. Pay attention to what happens at first:
  - Does it correctly identify what is needed to make a map?
    * It created a geographical heatmap of the Minneapolis-Twin Cities area and colored the different neighborhoods by a shading scheme, with darker shades representing more incident reports. 
  - Does it confuse attributes (like IDs) with coordinates?
    * It doesn't seem to have confused any attributes with coordinates as it counted the number of records using the data provided from the CSV. It converted the given lat/long coordinates to a project coordinate system suited to Minneapolis (EPSG:26915) to create a more appropriate proportion of the neighborhood boundaries/shapes. However, it did not verify if the location of the incident accurately was pinpointed in the appropriate neighborhood on the plot.


- For the scooter/e‑bike example, the goal is to join trips to a street or trail network such as the  
  [PW Street Centerline dataset](https://opendata.minneapolismn.gov/datasets/pw-street-centerline/about) and then map trip counts by segment.
- Identify a calculation, join, coordinate interpretation, or mapped value you could verify later. In Section 7.3, you will be asked to do some verification.
  * We could verify if the coordinates were assigned the correct interpretations using centerLong to X-axis and centerLat to Y-axis via the standardized GPS coordinate system (WGS84) so the points are focused in the Minneapolis-Twin Cities area.


**Task 5.1 (in `Codex_Activity.md`):**
Respond in 2–3 short bullets, considering:

- Describe what was easier and harder about doing this with Codex.
  * It was able to visualize the coordinates and flag the outliers in the data. But it was harder to see the structural data errors (like why Records 1, 6, and 9 share the same point) without digging more into the data.

- Where did Codex help, and where did it get in the way?
  * It was able to map the X- and Y-axes correctly with centerLong assigned to the X-axis and centerLat to Y-axis. It also made a spatial boundary check to isaolte Record 4 as an outlier and colored that point orange. However, it stopped there as it visually flagged that it was outside the boundary but didn't cross reference the text attributes to tell me where the underlying error lies, like whether it was due to the coordinate values, the neighborhood text string, etc.

- What would you do differently next time you had to map a new dataset with AI assistance?
  * Since it didn't audit or clean it up automatically, we had to step in to figure it out. So next time I would prompt the AI to write a more comprehensive quality check or some sort to isolate records with conflict and make sure this troubleshooting is done before it goes on to create and map the plot.  


# 6. Identifying a research question with Codex

- If you are partner coding, *switch partners*.
- You will now work with Codex to identify and refine a research question (RQ) about your dataset.
- Choose a question you can answer with the downloaded data and a small extension of your existing exploration or mapping code. A descriptive question is sufficient; aim for an analysis you can implement in about 20 minutes.

## 6.1 Brainstorm candidate questions

- Seed the brainstorming session with some themes or ideas of research questions that interest you.
- Ask Codex to propose several possible research questions.
- Collaborate with Codex to prioritize the questions along the decision dimensions you think are most appropriate.

**Task 6.1 (in `Codex_Activity.md`):**

- List at least two candidate research questions that Codex suggested.
- For each, briefly note what seems interesting and what might be problematic (data, scope, ethics, feasibility).
  * When certain geographic coordinates have had multiple police incident reports at the same exact location, what types of crime are most prevalent there?
    - Interesting: Coud show whether locations with many reports have distinct offense patterns
    - Problematic: Identical public coordiantes couls repersent approximate locations rather than the same exact incident site
  * What types of crime are most prevalent during the late-night weekend hours (i.e. Friday and Saturday, 11 PM to 4 AM) compared to daylight working hours (Monday through Fridaty, 9 AM to 5 PM), and what might this reveal about peak activity hours?"
    - Interesting: Could reveal differences in the mix of recorded offenses between nightlife hours and typical working hours
    - Problematic: Comparing incident reports between a 2-day weekend and a full 5-day work week ceover unequal durartions of time which would not be able to determine overall peak activity hours or explain why differences might exist. 

## 6.2 Refine and choose your question

- Pick one question (it may be a slight modification of a Codex suggestion).
- Ask Codex to critique and refine that question. For example:
  - “Here is my tentative research question: […]. Critique its clarity and feasibility. Propose 1–2 improved versions.”
- Decide on a **final RQ** you will try to answer. This choice is yours, not Codex’s.

**Task 6.2 (in `Codex_Activity.md`):**

- Write down your final research question in one clear sentence.
  * Among incidents with valid recorded start dates and times in January–September 2026, how do the most common offense descriptions and their percentage shares differ between Friday/Saturday nights, 11 PM–4 AM, and Monday–Friday working hours, 9 AM–5 PM?

- In 2–3 sentences, explain why you chose it (and why you rejected other candidates).
  * I chose this one as the other proposed version suggested looking at the frequency of the reports, but the type of common offense is more of an interesting question to look into. Although it would also be interesting to analyze what type of crime is most common at a highly reported location, I think that the question I chose would provide a broader look at the data and any significant patterns that could consequently give rise to more specific questions afterwards. 

# 7. Answering your question: plan, implement, and verify

Build on your exploration and map to answer **one research question**. Review a plan with Codex, implement it, and verify one important result or transformation.

## 7.1 Design and review a plan

**Plan mode** lets Codex inspect context, ask clarifying questions, and propose an approach before implementation. It can investigate existing files; it should not implement your analysis while planning. See the [OpenAI guidance on Plan mode](https://learn.chatgpt.com/docs/learn/best-practices).

1. Wait until Codex finishes its current response.
2. In the **Codex chat input inside VS Code**, enter `/plan`, select the command, and press Enter. Check that Plan mode is active. If using Codex CLI alongside RStudio, enter the command in the Codex conversation in your terminal.
3. Submit your planning request and answer any clarifying questions.
4. Review and revise the proposed plan before leaving Plan mode.

Review the plan yourself:

- Does it answer your chosen question using available data?
  * Yes, the proposed plan addresses the chosen research question by isolating "Weekend Nights" (Friday/Saturday 11 PM to 4 AM) and comparing them against "Working Hours" (Monday-Friday 9 AM to 5 PM) using the beginDate, beginTime, and description attributes/fields from the dataset.

- Are the units, filters, grouping, and treatment of missing values appropriate?
  * Yes, the time filters handle boundaries and grouping are set by offense description. Also, missing descriptions are kept as "Unknown" insteae of removing them which allows the total baseline count to remain the same and unskewed. 

- Does it reuse relevant exploration or mapping work?
  * Yes, the plan reuses the existing data exploration work, color schemes, and the matplotlib styling from the previous sections. 

- Is the proposed verification feasible and capable of detecting a meaningful error?
  * Yes, it is feasible due to just a simple manual calculation check which would involve counting up an offense type and dividing it by the total window count. There is also a sensitivity check to catch any structural errors like detecting for placeholder 00:00 times and if it artificially inflates the percentages.

Ask Codex to clarify or revise anything you cannot justify. If you do not understand the type of analysis or choices it is suggesting, stop! Discuss them with your partner and clarify with Codex.

**Task 7.1 (in `Codex_Activity.md`):**

- Record your final plan in 3–5 bullets.
  * Isolate Weekend Nights (Friday/Saturday, 23:00 to 04:00) and Working Hours (Monday through Friday, 09:00 to 17:00) using beginDate and beginTime.
  * Group the records by crime description, keep missing records categorized as "Unknown", and calculate each offense as a percentage of its specific time range/window.
  * Export data results and summaries to CSV tables and plot a comparative bar chart to show the top 5 most prevalent offenses for both windows. 
  * Do a sensitivity check by isolating and removing incidents that are recorded at exactly 00:00 to check if they are placeholders that might distort the late-night statistical results.
  * Verify the analysis by selecting a single offense type from a window to independently calculate its percentage-point and ensuring its accuracy under the recorded-clock assumption.


- Explain one decision you made while reviewing it. A justified decision to retain a proposed approach counts; you do not need to change the plan just to make a change. However, don't just blindly accept what it suggests. Stop and discuss each decision with your partner!
  * Decided to include Codex's proposal to make a sensitivty check at the midnight 00:00 time. The police data entries typically default to a placeholder time of 00:00 when the exact time of an incident is unknown, so processing that time blindly could have artificially inflated our nighttime crime results. So, including this sensitivity comparison without the 00:00 records lets us evaluate its accuracy and robustness before finalizing on any conclusions. 


## 7.2 Implement and inspect

Use the `/plan` toggle to leave Plan mode and confirm it is off **before** requesting implementation, or Press the "Implement this plan" option if it appears.

- You can request the whole small plan or start with a meaningful first step and continue after inspecting it.
- Keep the work in the R or Python analysis file.
- Inspect the changed code and outputs. Does the analysis answer your question? Are the results interpretable and relevant?
- Ask targeted follow-up questions and revise as needed. 

**Task 7.2 (in `Codex_Activity.md`):**

- Briefly state your result and link to the supporting figure, table, or code.
  * Codex compared 1,395 nighttime-weekend incidents against 4,219 daytime-workinghour incidents and the results revealed that property theft dominates in both windows. However, Automobile Theft peaks significantly during the weekend nights (21.5% vs. 17.1%), while Shoplifting theft exclusively happens during daytime and working hours (7.8% vs. 0.0%)

- Describe one implementation choice or issue you examined and what you decided about it.
  * I tried to look into the "Other theft" category as it was the most prevalent crime category during daytime working hours (20.7%) to see if Codex might have overly filtered too restrictively that might have caused the grouping of distinct sub-types of theft into a single category. However, after checking more of Codexs' output and the dataset file, I found that Codex had not done any filtering. There were 2,892 records that shared the same offense code THEFT and UCR code 07 with no further description of what kind of theft it was. Since this was an unmodifiable limitation from the raw dataset, this category could not be further investigated or broken down just from this dataset alone. So, the category had to be kept as-is but its lack of specificity needs to be noted. 


## 7.3 Verify one important result and reflect

Perform **one documented check** of a consequential claim, calculation, or transformation from your exploration, mapping, or final analysis. 

Choose a check suited to your dataset. Here are some possibilities you could consider:

| Check | Evidence you could provide |
|---|---|
| Recalculate a summary | Manually compute a count, mean, or percentage for a small identified subset and compare it with the code's result for that subset. |
| Check a join used in mapping | Inspect several known matches against the source records and account for unmatched or duplicated records. |
| Check mapped locations | Compare several identifiable features with an authoritative reference and record specific matches or discrepancies. |
| Check a derived variable | Use documented units and a few source records to calculate expected values independently and compare them with the derived values. |

Successful execution, a plausible-looking map, or Codex saying “this is correct” does not satisfy this requirement. Codex may help write checking code, but **you must explain the basis of the check and inspect its evidence**. Establish an expected result or reference independently of the output you are checking.

**Task 7.3 (in `Codex_Activity.md`):**

Record:

- **What I checked and why it matters.**
  * I checked the sensitivity check which isolated and excluded 216 midnight (00:00) entries from the weekend-night group which dropped the sample from 1,395 to 1,179 incidents. This matters because police reports would frequently default to a placeholder time of 00:00 if the time of a crime was unknown. By doing this check we were able to see whether those placeholder records affected or skewed our results in any way.
  
- **How I checked it**, including the independently established expectation or reference.
  * By looking over Codex's validation output from the 'time_window_verification.md' and cross-examining the percentage shifts, I was able to establish an expectation. If midnight entries hadheavy articifical placeholders for property crimes in the morning, removing them would cause a spike in assualt-type crimes that were usually reported immediately. 

- **What I observed**, with actual values, identified records, or another concrete comparison.
  * So when the 216 midnight records were removed, the top 3 nighttime-weekend crime categories, which were Automobile theft, Theft from motor vehicles, and Other theft, remained in the same order. However, the more immediate assuault-type offenses, particularly the Assault with a Dangerous Weapon category, gained enough statistical influence to displace the other lower-percentage categories, which was as expected.

- **What I changed or concluded**, including the result of rechecking any correction.
  * No changes were made to the codebase since the data entries are technically valid, though any conclusions from this analysis would need to note that it is based on the assumption that the time/clock values in the CSV file are correct ("recorded-clock assumption"). So the results are derived directly from the city's administrative records and should not be interpreted as an absolute ground-truth. However, under this assumption, the top three crime categories did remain stable and resilient against midnight rounding biases. So given that the administrative record data serves as our baseline, our findings would technically be robust.



# 8. What to hand in

By the end of the activity, your repo should include at least:

- `Codex_Activity.md` with answers to all **Task** prompts (3.1, 4.1, 5.1, 6.1, 6.2, 7.1, 7.2, 7.3), including your reviewed plan, research-question result, and verification evidence.
- At least one analysis file:
  - R: `analysis/codex_activity.qmd` or `analysis/codex_activity.R`
  - Python: `analysis/codex_activity.ipynb` or `analysis/codex_activity.py`
- At least one map saved in the repo and linked from your writeup, or embedded in your analysis/writeup.
- Any additional scripts or notebooks you used, committed in a reasonable state.

Before you’re done:

- Use Codex to help you **commit and push** your work to your forked repo.
- Make sure that your API key is **not** anywhere in the repo.
- Share the URL for the repo (including the markdown and script) on the Moodle activity.
