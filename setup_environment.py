import pandas as pd
import os
import requests
import json
import logging
import time

# ===============================
# LOGGING
# ===============================
logger = logging.getLogger(__name__)

# ===============================
# LLM CLIENT (SINGLE SOURCE OF TRUTH)
# ===============================

class BoschLLMClient:
    """Centralized LLM client with timeout, retry, and error handling."""

    def __init__(self):
        self.api_key = os.getenv("BOSCH_LLM_API_KEY")

        self.url = (
            "https://aoai-farm.bosch-temp.com/api/openai/deployments/"
            "askbosch-prod-farm-openai-gpt-4o-mini-2024-07-18/chat/completions"
            "?api-version=2024-08-01-preview"
        )

        self.headers = {
            "Content-Type": "application/json",
            "genaiplatform-farm-subscription-key": self.api_key
        }

    def chat(self, messages, max_tokens=200, temperature=0.2, retries=2):
        """Send chat request with timeout and retry logic."""
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        last_error = None
        for attempt in range(retries + 1):
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]

            except requests.Timeout:
                last_error = "AI service timed out"
                logger.warning(f"LLM timeout (attempt {attempt + 1}/{retries + 1})")
            except requests.ConnectionError:
                last_error = "Cannot reach AI service"
                logger.warning(f"LLM connection error (attempt {attempt + 1}/{retries + 1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM error (attempt {attempt + 1}/{retries + 1}): {e}")

            if attempt < retries:
                time.sleep(1)

        logger.error(f"LLM call failed after {retries + 1} attempts: {last_error}")
        return f"⚠️ AI unavailable: {last_error}"


llm = BoschLLMClient()

# ===============================
# SUMMARY AGENT
# ===============================

def generate_daily_brief(data):

    df = pd.DataFrame(data)

    if df.empty:
        return "No deviation data available."

    dominant_line = df["line"].value_counts().idxmax()
    dominant_station = df["station"].value_counts().idxmax()
    dominant_principle = df["ai_principle"].value_counts().idxmax()
    dominant_flm = df["supervisor"].value_counts().idxmax()

    message = f"""
Hi All,

Below are the key highlights:

1. Increase in {dominant_principle} issues at Station {dominant_station} (Line {dominant_line}).
2. Majority of deviations observed during {dominant_flm}'s shift.

Action: {dominant_flm} to conduct focused line walk at Station {dominant_station} and ensure proper control of {dominant_principle.lower()}. 
Follow-up review in next shift to confirm issue closure.
"""

    return message.strip()


def generate_weekly_brief(current_data, previous_data):

    current_df = pd.DataFrame(current_data)
    previous_df = pd.DataFrame(previous_data)

    if current_df.empty:
        return "No deviation data available."

    # Basic metrics
    dominant_principle = current_df["ai_principle"].value_counts().idxmax()
    dominant_station = current_df["station"].value_counts().idxmax()
    dominant_flm = current_df["supervisor"].value_counts().idxmax()

    # Trend
    if len(current_df) > len(previous_df):
        trend = "increase in overall deviations"
    elif len(current_df) < len(previous_df):
        trend = "overall improvement compared to last week"
    else:
        trend = "stable condition compared to last week"

    prompt = f"""
You are preparing a simple weekly management brief.

Data Insights:
- Trend: {trend}
- Dominant Issue: {dominant_principle}
- Hotspot Station: {dominant_station}
- Majority Shift: {dominant_flm}

Instructions:
- Start with: "Hi All,"
- Then: "Below are the key weekly highlights:"
- Provide 2 to 5 short bullet points only
- Do NOT repeat principle code if issue name already clear (avoid saying 1C again)
- Use neutral language (do not blame individuals)
- Instead of saying 'responsible', say 'most cases observed during'
- Keep language simple and direct
- No technical explanation
- No percentages
- Final section must start with: "Action:"
- Action must include:
    • focused line walk
    • reinforcement of control at hotspot station
    • shift-level accountability
- Do NOT use weak words like 'monitor closely'

Keep concise and management-friendly.
"""

    response = llm.chat([
        {"role": "system", "content": "You create simple management-friendly operational briefs."},
        {"role": "user", "content": prompt}
    ])

    return response


def generate_monthly_brief(current_data, previous_data):

    current_df = pd.DataFrame(current_data)
    previous_df = pd.DataFrame(previous_data)

    if current_df.empty:
        return "No deviation data available."

    dominant_principle = current_df["ai_principle"].value_counts().idxmax()
    dominant_station = current_df["station"].value_counts().idxmax()
    dominant_flm = current_df["supervisor"].value_counts().idxmax()

    # Determine simple trend
    if len(current_df) > len(previous_df):
        trend = "discipline gaps increased this month"
    elif len(current_df) < len(previous_df):
        trend = "discipline condition improved this month"
    else:
        trend = "discipline condition remained stable"

    prompt = f"""
You are preparing a simple monthly management overview.

Key Inputs:
- Overall Trend: {trend}
- Major Recurring Issue: {dominant_principle}
- Chronic Station: {dominant_station}
- Majority Shift Linkage: {dominant_flm}

Instructions:
- Start with: "Hi All,"
- Then: "Below are the key monthly highlights:"
- Provide 2 to 5 short bullet points
- Avoid repeating principle codes unnecessarily
- Do NOT use accusatory tone
- Use neutral phrasing like:
    'Repeated observations noted during {dominant_flm}'s shift'
- Focus on pattern and location
- No consultant language
- No strategic buzzwords
- Keep language operational

Final section must start with: "Action:"
- Action must:
    • assign ownership clearly
    • define structural correction
    • strengthen control system
    • not say 'monitor' or 'review'
    • not sound weak

Keep concise and leadership-ready.
"""

    response = llm.chat([
        {"role": "system", "content": "You generate simple leadership-ready monthly operational briefs."},
        {"role": "user", "content": prompt}
    ])

    return response


def generate_mail_from_summary(summary_text, mail_type="Daily"):

    prompt = f"""
Convert the following audit summary into a professional email.

Rules:
- Keep content SAME (do not add new insights)
- Just structure properly into email format
- Add Subject line
- Start with "Hi All,"
- Keep clean spacing and readability
- Add closing: "Best regards,"
- Keep concise and professional

Summary:
{summary_text}
"""

    response = llm.chat([
        {"role": "system", "content": "You format summaries into professional emails."},
        {"role": "user", "content": prompt}
    ])

    return response

# ===============================
# AGENT 2 (AUDIT PLAN)
# ===============================

def classify_by_percentile(risk_df):
    risk_df = risk_df.sort_values(by="risk_score", ascending=False).reset_index(drop=True)

    n = len(risk_df)
    risk_df["rank"] = risk_df.index + 1
    risk_df["percentile"] = risk_df["rank"] / n

    def classify(p):
        if p <= 0.2:
            return "Very High", 4
        elif p <= 0.5:
            return "High", 3
        elif p <= 0.8:
            return "Medium", 2
        else:
            return "Stable", 1

    risk_df[["risk_level","audit_frequency"]] = risk_df["percentile"].apply(
        lambda x: pd.Series(classify(x))
    )

    return risk_df


def generate_governance_annual_plan(risk_df):
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    plan_rows = []

    for _, row in risk_df.iterrows():
        line = f"Line {row['LINE']}"
        risk = row["risk_level"]

        month_map = {m: "" for m in months}

        if risk == "Very High":
            selected = ["Jan","Apr","Jul","Oct"]
        elif risk == "High":
            selected = ["Feb","Jun","Oct"]
        elif risk == "Medium":
            selected = ["May","Sep"]
        else:
            selected = ["Nov"]

        for m in selected:
            month_map[m] = "X"

        plan_rows.append({
            "Line": line,
            "Risk Level": risk,
            **month_map
        })

    return pd.DataFrame(plan_rows)

# ===============================
# AGENT 3
# ===============================
def get_iatf_clause_mapping():

    return {
        "1C – Cleanliness": ("8.5.1", "Control of Production and Service Provision"),
        "Remaining Items": ("8.5.1", "Control of Production and Service Provision"),
        "Correct Product": ("8.5.1", "Control of Production and Service Provision"),
        "Dropped Parts": ("8.7.1", "Control of Nonconforming Outputs"),
        "Rework / Scrap": ("8.7.1", "Control of Nonconforming Outputs"),
        "Labeling": ("8.5.2", "Identification and Traceability"),
        "Measurement / Test Equipment": ("7.1.5", "Monitoring and Measuring Resources"),
        "Instructions": ("7.5.1", "Documented Information"),
        "Process Parameters": ("8.5.1", "Control of Production and Service Provision"),
        "Tools": ("8.5.1", "Control of Production and Service Provision"),
        "Check the Checker": ("9.1.1", "Monitoring, Measurement, Analysis and Evaluation"),
        "Restart": ("8.5.1", "Control of Production and Service Provision"),
        "Stop Sign": ("10.2", "Nonconformity and Corrective Action"),
        "Andon Cord": ("10.2", "Nonconformity and Corrective Action"),
        "Total Productive Maintenance (TPM)": ("8.5.1.5", "Total Productive Maintenance")
    }

def generate_guided_audit_questions(line, deviation_data, iqis_df, top_n=3):

    clause_map = get_iatf_clause_mapping()

    def normalize_line(val):
        try:
            return str(int(float(val)))
        except (ValueError, TypeError):
            return str(val).strip().replace("Line ", "")

    line_devs = [
        d for d in deviation_data
        if normalize_line(d.get("line")) == normalize_line(line)
    ]

    if not line_devs:
        return "No deviation data available for this line."

    df_dev = pd.DataFrame(line_devs)

    # Dominant principle
    dominant_principle = df_dev["ai_principle"].value_counts().idxmax()

    # Top stations
    top_stations = df_dev["station"].value_counts().head(3).index.tolist()
    top_stations_str = ", ".join(top_stations)

    # Top deviations
    top_deviations = df_dev["observation_text"].value_counts().head(top_n).to_dict()

    # Responsible supervisor
    flm = df_dev["supervisor"].value_counts().idxmax()

    # Clause mapping
    clause_number, clause_title = clause_map.get(
        dominant_principle,
        ("8.5.1", "Control of Production and Service Provision")
    )

    structured_context = f"""
Line: {line}
Dominant Discipline Gap: {dominant_principle}
IATF Clause: {clause_number} – {clause_title}
Critical Stations: {top_stations_str}
Responsible FLM: {flm}

Top Recurring Deviations:
{top_deviations}
"""

    prompt = f"""
You are a senior IATF 16949 process audit expert preparing plant-floor audit questions.

Context:
{structured_context}

Strict Output Format:

Clause {clause_number} – {clause_title}

1. Question
2. Question
3. Question
...
6–8 questions total

Then final section:

Audit Objective:

Rules:

- Questions must verify **actual process control**, not only documentation.
- Focus on **physical conditions, operator behavior, and station control**.
- Avoid phrases like:
  "Is there a documented procedure"
  "Are records available"
  "Show documentation"

- Use varied audit verbs:
  Is, Are, Does, Verify, Confirm, Check, Ensure, Assess.

- Each question must reference **Line {line} – Station XX**.
- Distribute questions across stations: {top_stations_str}.
- At least one question must verify **escalation or stop-rule**.
- At least one question must verify **FLM supervision by {flm}**.
- Questions must directly relate to these observed deviations:
  {top_deviations}
- Must ensure that line and station number are present.
- Keep each question short (one sentence).
- Maintain professional audit tone suitable for certification audit.
- Make questions executable during plant-floor audit.

Audit Objective rules:

- One concise sentence.
- Must reference Clause {clause_number}.
- Must reference the discipline gap: {dominant_principle}.
- Must reference Line {line}.
- Must mention preventing recurrence of the observed deviation.

Do not include any explanation outside the required format.
"""

    response = llm.chat([
        {"role": "system", "content": "You generate plant-floor focused IATF audit questions."},
        {"role": "user", "content": prompt}
    ])

    return response

def generate_qcheck_questions(line, deviation_data, max_questions=15):

    # ==========================
    # STEP 1: FILTER DATA
    # ==========================
    filtered = [
        row for row in deviation_data
        if str(row.get("line")) == str(line)
    ]

    if not filtered:
        return []

    # ==========================
    # STEP 2: SORT BY RECENCY
    # ==========================
    filtered = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    # ==========================
    # STEP 3: PICK UNIQUE ISSUES (avoid duplicates)
    # ==========================
    seen = set()
    selected = []

    for row in filtered:
        key = (row.get("station"), row.get("observation_text"))

        if key not in seen:
            seen.add(key)
            selected.append(row)

        if len(selected) >= max_questions:
            break

    # ==========================
    # STEP 4: PREPARE PROMPT (BATCH)
    # ==========================
    observations = [
        f"{i+1}. {row['observation_text']}"
        for i, row in enumerate(selected)
    ]

    prompt = f"""
Convert the following manufacturing deviations into short audit checkpoint questions.

Rules:
- One sentence per question
- Yes/No type
- Do NOT mention line or station
- Keep it short and practical for plant-floor audit
- Maintain professional audit tone

Deviations:
{chr(10).join(observations)}

Return output as numbered list only.
"""

    # ==========================
    # STEP 5: LLM CALL
    # ==========================
    response = llm.chat([
        {"role": "system", "content": "You generate short plant-floor audit checkpoints."},
        {"role": "user", "content": prompt}
    ])

    content = response

    # ==========================
    # STEP 6: PARSE RESPONSE
    # ==========================
    questions = []

    lines = content.split("\n")

    q_index = 0
    for line_text in lines:
        line_text = line_text.strip()

        if line_text and any(char.isdigit() for char in line_text[:3]):
            # remove numbering like "1. "
            q = line_text.split(".", 1)[-1].strip()

            if q_index < len(selected):
                row = selected[q_index]

                questions.append({
                    "Station": row["station"],
                    "Checkpoint": q,
                    "Ref Photo": "",   
                    "Status": "OK",
                    "Remark": ""   
                })

                q_index += 1

    return questions

# ===============================
# AGENT 4
# ===============================

def generate_iatf_process_audit_sheet(line, deviation_data, iqis_df, lpc_df, top_n=3):

    # ----------------------------
    # 1. FILTER DATA
    # ----------------------------
    df_dev = pd.DataFrame(deviation_data)
    df_dev_line = df_dev[df_dev["line"].astype(str) == str(line)]

    if df_dev_line.empty:
        return "No deviation data available for this line."

    # ----------------------------
    # 2. CLAUSE MAP
    # ----------------------------
    clause_map = {
        "Cleanliness": ("8.5.1", "Control of Production"),
        "Stop Sign": ("10.2", "Corrective Action"),
        "Andon Cord": ("8.5.1", "Control of Production"),
        "Instructions": ("7.5", "Documented Information"),
        "Process Parameters": ("8.5.1", "Control of Production"),
        "Measurement / Test Equipment": ("7.1.5", "Monitoring & Measuring"),
        "Check the Checker": ("9.1.1", "Performance Evaluation"),
        "Total Productive Maintenance (TPM)": ("8.5.1.5", "TPM"),
        "Tools": ("8.5.1.5", "TPM"),
        "Restart": ("8.5.1", "Control of Production"),
        "Labeling": ("8.5.2", "Identification & Traceability"),
        "Rework / Scrap": ("8.7", "Nonconforming Output"),
        "Dropped Parts": ("8.7", "Nonconforming Output"),
        "Correct Product": ("8.5.1", "Control of Production"),
        "Remaining Items": ("8.5.4", "Preservation")
    }

    # ----------------------------
    # 3. IDENTIFY TOP STATIONS
    # ----------------------------
    station_counts = df_dev_line["station"].value_counts()
    top_stations = station_counts.head(top_n).index.tolist()

    final_rows = []

    for station in top_stations:

        df_station = df_dev_line[df_dev_line["station"] == station]

        top_issue = df_station["observation_text"].value_counts().idxmax()
        principle = df_station["ai_principle"].value_counts().idxmax()

        # Clean principle text
        if "–" in principle:
            principle_key = principle.split("–")[1].strip()
        else:
            principle_key = principle.strip()

        clause, clause_title = clause_map.get(
            principle_key, ("8.5.1", "Control of Production")
        )

        # Simple audit checkpoint
        checkpoint = f"Verify Line {line} – Station {station} control for {principle_key}."

        final_rows.append({
            "Clause": clause,
            "Clause_Title": clause_title,
            "Line": line,
            "Station": station,
            "Process_Risk": top_issue,
            "Audit_Check_Point": checkpoint,
            "Audit_Status": "",
            "Remarks": ""
        })

    df_audit = pd.DataFrame(final_rows)

    logger.info(f"IATF Process Audit Checksheet Generated – Line {line}")

    return df_audit


# ===============================
# AGENT 5
# ===============================
def generate_followup_checklist(line, agent3_df):

    if agent3_df is None or agent3_df.empty:
        return "No audit data available."

    followup_rows = []

    for _, row in agent3_df.iterrows():

        station = row["Station"]
        issue = row["Process_Risk"]

        # Get recurrence count if available
        if "Recurrence_Count" in agent3_df.columns:
            recurrence = row["Recurrence_Count"]
        else:
            recurrence = 1  # Default if column not present

        followup_rows.append({
            "Line": line,
            "Station": station,
            "Issue": issue,
            "Previous_Occurrence_Count": recurrence,
            "Follow_Up_Check": f"Verify that '{issue}' at Station {station} is corrected and not repeated.",
            "Status (Yes/No)": "",
            "Remarks": ""
        })

    df_followup = pd.DataFrame(followup_rows)

    logger.info(f"Follow-Up Checklist Generated – Line {line}")

    return df_followup


# ===============================
# AGENT 6
# ===============================
def generate_external_audit_tracker_with_ai(deviation_data, top_n=5):

    df = pd.DataFrame(deviation_data)

    if df.empty:
        return "No historical deviation data available."

    grouped = (
        df.groupby(["line", "station", "observation_text"])
        .size()
        .reset_index(name="Recurrence_Count")
        .sort_values(by="Recurrence_Count", ascending=False)
    )

    top_issues = grouped.head(top_n)

    tracker_rows = []

    for _, row in top_issues.iterrows():

        line = row["line"]
        station = row["station"]
        issue = row["observation_text"]
        recurrence = row["Recurrence_Count"]

        # AI Suggested Action
        prompt = f"""
You are an external IATF auditor.

Issue observed during audit:
Line {line} – Station {station}
Issue: {issue}
Recurrence Count: {recurrence}

Suggest one practical corrective action that the plant should implement.

Requirements:
- Keep simple and practical
- Maximum 1 lines
- Action must prevent recurrence
- Avoid technical jargon
- Suitable for plant-level execution
"""

        action_response = llm.chat([
            {"role": "system", "content": "You suggest practical corrective actions for manufacturing audit findings."},
            {"role": "user", "content": prompt}
        ])

        tracker_rows.append({
            "Line": line,
            "Station": station,
            "Issue_Raised_Last_Audit": issue,
            "Recurrence_Count": recurrence,
            "Action_To_Be_Taken (Suggested)": action_response.strip(),
            "Current_Status (Solved / Ongoing / Not Started)": "",
            "External_Auditor_Remarks": ""
        })

    df_tracker = pd.DataFrame(tracker_rows)

    logger.info("External Audit Governance Tracker Generated (AI Action Suggested)")

    return df_tracker


# ===============================
# AGENT 7 — DEVIATION CATEGORY
# ===============================
def map_deviation_category_ai(observations):

    # ==========================
    # PREPARE INPUT
    # ==========================
    obs_list = [f"{i+1}. {obs}" for i, obs in enumerate(observations)]

    prompt = f"""
Group the following manufacturing audit observations into standardized deviation categories.

Rules:
- Group similar meaning observations into ONE category
- Keep category names short (2–4 words)
- Use industrial terminology
- Avoid duplicates
- Return output as numbered list:
  Observation Number → Category Name

Observations:
{chr(10).join(obs_list)}
"""

    response = llm.chat([
        {"role": "system", "content": "You are an expert in manufacturing audit classification."},
        {"role": "user", "content": prompt}
    ])

    # ==========================
    # PARSE RESPONSE
    # ==========================
    mapping = {}

    lines = response.split("\n")

    for line in lines:
        if "→" in line:
            try:
                left, right = line.split("→")
                idx = int(left.strip().split(".")[0]) - 1
                category = right.strip()
                mapping[idx] = category
            except (ValueError, IndexError):
                continue

    # ==========================
    # RETURN CATEGORY LIST
    # ==========================
    categorized = []
    for i in range(len(observations)):
        categorized.append(mapping.get(i, "Other Issue"))

    return categorized