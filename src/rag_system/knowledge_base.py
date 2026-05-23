"""
Medical Knowledge Base - English
Comprehensive medical information for common diseases
"""

MEDICAL_KNOWLEDGE = {
    "pneumonia": {
        "name": "Pneumonia",
        "category": "Respiratory Infection",
        "description": "Pneumonia is an infection that inflames the air sacs in one or both lungs. The air sacs may fill with fluid or pus, causing cough with phlegm or pus, fever, chills, and difficulty breathing.",
        "symptoms": [
            "Cough with phlegm or pus",
            "Fever, sweating and shaking chills",
            "Shortness of breath",
            "Chest pain when breathing or coughing",
            "Fatigue and muscle aches",
            "Nausea, vomiting or diarrhea",
            "Confusion (especially in older adults)"
        ],
        "causes": [
            "Bacteria (Streptococcus pneumoniae most common)",
            "Viruses including COVID-19",
            "Fungi (less common)"
        ],
        "risk_factors": [
            "Age under 2 or over 65",
            "Weakened immune system",
            "Chronic diseases (asthma, COPD, heart disease)",
            "Smoking",
            "Hospitalization"
        ],
        "diagnosis": [
            "Chest X-ray",
            "Blood tests",
            "Pulse oximetry",
            "Sputum test",
            "CT scan (if severe)"
        ],
        "treatment": [
            "Antibiotics for bacterial pneumonia",
            "Antivirals for viral pneumonia",
            "Fever reducers and pain relievers",
            "Cough medicine",
            "Rest and fluids",
            "Hospitalization if severe"
        ],
        "prevention": [
            "Vaccination (pneumococcal vaccine, flu vaccine)",
            "Good hygiene practices",
            "Don't smoke",
            "Maintain healthy lifestyle"
        ],
        "xray_findings": "Consolidation, infiltrates, or opacity in lung fields"
    },
    
    "covid19": {
        "name": "COVID-19",
        "category": "Viral Respiratory Disease",
        "description": "COVID-19 is a respiratory illness caused by the SARS-CoV-2 virus. It can range from mild symptoms to severe illness requiring hospitalization.",
        "symptoms": [
            "Fever or chills",
            "Cough (usually dry)",
            "Shortness of breath or difficulty breathing",
            "Fatigue",
            "Muscle or body aches",
            "Headache",
            "Loss of taste or smell",
            "Sore throat",
            "Congestion or runny nose",
            "Nausea or vomiting",
            "Diarrhea"
        ],
        "causes": [
            "SARS-CoV-2 virus infection",
            "Spread through respiratory droplets",
            "Close contact with infected persons",
            "Contaminated surfaces (less common)"
        ],
        "risk_factors": [
            "Older age (65+)",
            "Chronic lung disease",
            "Heart conditions",
            "Diabetes",
            "Obesity",
            "Immunocompromised state",
            "Unvaccinated status"
        ],
        "diagnosis": [
            "RT-PCR test (nasal swab)",
            "Rapid antigen test",
            "Chest X-ray or CT scan",
            "Blood tests",
            "Pulse oximetry"
        ],
        "treatment": [
            "Isolation and rest",
            "Fever reducers (acetaminophen)",
            "Antivirals (Paxlovid, Remdesivir) for high-risk patients",
            "Monoclonal antibodies (in some cases)",
            "Oxygen therapy if needed",
            "Hospitalization for severe cases",
            "Ventilation if critical"
        ],
        "prevention": [
            "Vaccination",
            "Wear masks in crowded areas",
            "Social distancing",
            "Hand hygiene",
            "Ventilation in indoor spaces",
            "Avoid close contact with sick people"
        ],
        "xray_findings": "Ground-glass opacities, bilateral infiltrates, peripheral distribution"
    },
    
    "tuberculosis": {
        "name": "Tuberculosis (TB)",
        "category": "Bacterial Infection",
        "description": "Tuberculosis is a serious infectious disease that mainly affects the lungs. It is caused by Mycobacterium tuberculosis bacteria and spreads through the air when infected people cough or sneeze.",
        "symptoms": [
            "Persistent cough (3+ weeks)",
            "Coughing up blood or sputum",
            "Chest pain",
            "Unintentional weight loss",
            "Fatigue and weakness",
            "Fever",
            "Night sweats",
            "Chills",
            "Loss of appetite"
        ],
        "causes": [
            "Mycobacterium tuberculosis bacteria",
            "Airborne transmission from infected individuals",
            "Close contact in crowded conditions"
        ],
        "risk_factors": [
            "HIV infection",
            "Weak immune system",
            "Diabetes",
            "Kidney disease",
            "Malnutrition",
            "Close contact with TB patients",
            "Healthcare workers",
            "Living in endemic areas"
        ],
        "diagnosis": [
            "Tuberculin skin test (TST)",
            "Interferon-gamma release assays (IGRAs)",
            "Chest X-ray",
            "Sputum smear microscopy",
            "Sputum culture",
            "GeneXpert MTB/RIF test",
            "CT scan"
        ],
        "treatment": [
            "Combination antibiotic therapy (6-9 months)",
            "First-line drugs: Isoniazid, Rifampin, Ethambutol, Pyrazinamide",
            "Directly observed therapy (DOT)",
            "Isolation during infectious period",
            "Treatment of latent TB to prevent active disease"
        ],
        "prevention": [
            "BCG vaccine (in endemic countries)",
            "Proper ventilation",
            "Infection control in healthcare settings",
            "Early detection and treatment",
            "Preventive therapy for high-risk individuals"
        ],
        "xray_findings": "Upper lobe infiltrates, cavitation, nodules, fibrosis"
    },
    
    "normal": {
        "name": "Normal Chest X-ray",
        "category": "Healthy",
        "description": "A normal chest X-ray shows clear lung fields with no signs of infection, inflammation, or abnormal masses.",
        "characteristics": [
            "Clear, well-aerated lung fields",
            "Sharp costophrenic angles",
            "Normal heart size and shape",
            "Clear trachea and bronchi",
            "No infiltrates or consolidations",
            "Normal bone structures"
        ],
        "interpretation": "No acute cardiopulmonary disease evident",
        "recommendation": "Maintain healthy lifestyle and regular check-ups"
    },
    
    "cardiomegaly": {
        "name": "Cardiomegaly",
        "category": "Cardiac Condition",
        "description": "Cardiomegaly is an enlarged heart, which can be a sign of various underlying conditions affecting the heart muscle or valves.",
        "symptoms": [
            "Shortness of breath",
            "Fatigue",
            "Swelling in legs and ankles",
            "Irregular heartbeat",
            "Chest discomfort",
            "Dizziness or fainting"
        ],
        "causes": [
            "High blood pressure (hypertension)",
            "Heart valve disease",
            "Cardiomyopathy",
            "Coronary artery disease",
            "Heart attack history",
            "Congenital heart defects"
        ],
        "diagnosis": [
            "Chest X-ray (cardiothoracic ratio > 0.5)",
            "Echocardiogram",
            "ECG",
            "Stress test",
            "Cardiac MRI or CT",
            "Blood tests"
        ],
        "treatment": [
            "Treat underlying cause",
            "Medications (ACE inhibitors, beta-blockers, diuretics)",
            "Lifestyle changes",
            "Surgery or devices (in some cases)",
            "Regular monitoring"
        ],
        "xray_findings": "Enlarged cardiac silhouette, increased cardiothoracic ratio"
    },
    
    "pleural_effusion": {
        "name": "Pleural Effusion",
        "category": "Respiratory Condition",
        "description": "Pleural effusion is the accumulation of excess fluid between the layers of the pleura (membranes lining the lungs and chest cavity).",
        "symptoms": [
            "Shortness of breath",
            "Chest pain (especially when breathing)",
            "Dry cough",
            "Fever (if infection present)",
            "Difficulty lying flat"
        ],
        "causes": [
            "Heart failure",
            "Pneumonia",
            "Cancer",
            "Pulmonary embolism",
            "Kidney disease",
            "Liver cirrhosis",
            "Autoimmune diseases"
        ],
        "diagnosis": [
            "Chest X-ray",
            "CT scan",
            "Ultrasound",
            "Thoracentesis (fluid analysis)",
            "Pleural biopsy"
        ],
        "treatment": [
            "Treat underlying condition",
            "Thoracentesis (fluid drainage)",
            "Chest tube insertion",
            "Pleurodesis (for recurrent cases)",
            "Medications (diuretics, antibiotics if infected)"
        ],
        "xray_findings": "Blunting of costophrenic angles, fluid meniscus, opacification of hemithorax"
    },
    
    "atelectasis": {
        "name": "Atelectasis",
        "category": "Lung Collapse",
        "description": "Atelectasis is the partial or complete collapse of a lung or a section (lobe) of a lung, occurring when the tiny air sacs (alveoli) within the lung deflate or fill with fluid.",
        "symptoms": [
            "Difficulty breathing",
            "Rapid, shallow breathing",
            "Coughing",
            "Chest pain",
            "Low oxygen levels"
        ],
        "causes": [
            "Airway obstruction (mucus plug, tumor)",
            "Post-surgical complications",
            "Prolonged bed rest",
            "Shallow breathing",
            "Lung diseases",
            "Pressure from pleural effusion or pneumothorax"
        ],
        "diagnosis": [
            "Chest X-ray",
            "CT scan",
            "Bronchoscopy",
            "Oximetry"
        ],
        "treatment": [
            "Chest physiotherapy",
            "Deep breathing exercises",
            "Incentive spirometry",
            "Bronchoscopy (to remove obstruction)",
            "Positive pressure ventilation",
            "Medications to open airways"
        ],
        "xray_findings": "Increased opacity, volume loss, displacement of fissures, elevated hemidiaphragm"
    },
    
    "infiltration": {
        "name": "Pulmonary Infiltrate",
        "category": "Lung Abnormality",
        "description": "Pulmonary infiltrate refers to a substance denser than air (such as pus, blood, or protein) that fills the alveoli or interstitial spaces in the lung.",
        "symptoms": [
            "Cough",
            "Shortness of breath",
            "Fever (if infectious)",
            "Chest discomfort",
            "Abnormal breath sounds"
        ],
        "causes": [
            "Pneumonia (bacterial, viral, fungal)",
            "Tuberculosis",
            "Pulmonary edema",
            "Aspiration",
            "Lung cancer",
            "Interstitial lung disease",
            "Hemorrhage"
        ],
        "diagnosis": [
            "Chest X-ray",
            "CT scan",
            "Sputum culture",
            "Bronchoscopy with biopsy",
            "Blood tests"
        ],
        "treatment": [
            "Depends on underlying cause",
            "Antibiotics for infection",
            "Diuretics for pulmonary edema",
            "Oxygen therapy",
            "Treatment of underlying disease"
        ],
        "xray_findings": "Patchy or diffuse opacity, air bronchograms, interstitial markings"
    },
    
    "asthma": {
        "name": "Asthma",
        "category": "Chronic Respiratory Disease",
        "description": "Asthma is a chronic inflammatory condition of the airways characterized by variable airflow obstruction, bronchial hyperresponsiveness, and inflammation.",
        "symptoms": [
            "Wheezing",
            "Shortness of breath",
            "Chest tightness or pain",
            "Coughing (especially at night or during exercise)",
            "Difficulty speaking or exercising",
            "Anxiety about breathing"
        ],
        "causes": [
            "Genetic predisposition",
            "Allergies",
            "Environmental triggers (pollution, smoking)",
            "Respiratory infections",
            "Exercise-induced bronchoconstriction",
            "Occupational exposures"
        ],
        "treatment": [
            "Inhaled corticosteroids",
            "Beta-2 agonists (rescue inhalers)",
            "Long-acting bronchodilators",
            "Leukotriene modifiers",
            "Allergen avoidance",
            "Emergency care for acute attacks"
        ],
        "prevention": [
            "Avoid identified triggers",
            "Regular monitoring and peak flow measurement",
            "Adequate sleep and stress management",
            "Vaccinations (flu, pneumococcal)",
            "Maintain healthy weight"
        ]
    },
    
    "bronchitis": {
        "name": "Bronchitis",
        "category": "Respiratory Infection",
        "description": "Bronchitis is inflammation of the bronchial tubes that carry air to the lungs, characterized by a persistent cough and mucus production.",
        "symptoms": [
            "Persistent cough lasting weeks",
            "Mucus production (clear, white, or yellow)",
            "Fatigue and weakness",
            "Shortness of breath",
            "Mild fever and chills",
            "Chest discomfort",
            "Wheezing"
        ],
        "causes": [
            "Viral infections (similar to common cold)",
            "Bacterial infections (secondary)",
            "Smoking and secondhand smoke exposure",
            "Air pollutants and irritants",
            "Occupational dust exposure"
        ],
        "treatment": [
            "Rest and adequate hydration",
            "Cough suppressants or expectorants",
            "Bronchodilators to ease breathing",
            "Inhaled corticosteroids",
            "Antibiotics if bacterial",
            "Humidified air"
        ]
    },
    
    "pneumothorax": {
        "name": "Pneumothorax",
        "category": "Lung Collapse",
        "description": "Pneumothorax is the presence of air in the pleural space, causing partial or complete lung collapse.",
        "symptoms": [
            "Sudden sharp chest pain",
            "Sudden shortness of breath",
            "Rapid heart rate",
            "Decreased oxygen saturation",
            "Shoulder pain (in some cases)"
        ],
        "causes": [
            "Bullae rupture (spontaneous)",
            "Trauma or injury to chest",
            "Mechanical ventilation complications",
            "Underlying lung disease",
            "Marfan syndrome",
            "COPD exacerbation"
        ],
        "diagnosis": [
            "Chest X-ray (definitive)",
            "CT scan (for small pneumothorax)",
            "Vital signs monitoring",
            "Pulse oximetry",
            "Blood gas analysis"
        ],
        "treatment": [
            "Observation (for small, asymptomatic pneumothorax)",
            "Oxygen therapy",
            "Needle aspiration",
            "Chest tube insertion (for larger or symptomatic)",
            "Positive pressure ventilation",
            "Surgical intervention (for recurrent cases)"
        ],
        "xray_findings": "Collapsed lung with visceral pleural line, absent lung markings peripherally"
    },
    
    "copd": {
        "name": "COPD (Chronic Obstructive Pulmonary Disease)",
        "category": "Chronic Respiratory Disease",
        "description": "COPD is a progressive lung disease characterized by persistent airflow limitation including emphysema and chronic bronchitis.",
        "symptoms": [
            "Chronic cough with sputum production",
            "Shortness of breath, especially during physical activity",
            "Wheezing",
            "Chest tightness",
            "Fatigue",
            "Frequent respiratory infections",
            "Blue lips or fingernail beds (in severe cases)"
        ],
        "causes": [
            "Smoking (primary cause)",
            "Secondhand smoke exposure",
            "Occupational exposures",
            "Indoor air pollution",
            "Alpha-1 antitrypsin deficiency (genetic)"
        ],
        "risk_factors": [
            "Smoking history",
            "Age over 40",
            "Male gender",
            "Genetic factors",
            "Chronic air pollution exposure"
        ],
        "treatment": [
            "Smoking cessation",
            "Bronchodilators (beta-2 agonists, anticholinergics)",
            "Inhaled corticosteroids",
            "Phosphodiesterase-4 inhibitors",
            "Oxygen therapy",
            "Pulmonary rehabilitation"
        ]
    },
    
    "pulmonary_edema": {
        "name": "Pulmonary Edema",
        "category": "Respiratory Condition",
        "description": "Pulmonary edema is the abnormal accumulation of fluid in the lungs, impairing gas exchange and often causing acute respiratory distress.",
        "symptoms": [
            "Severe shortness of breath",
            "Orthopnea (difficulty breathing when lying down)",
            "Paroxysmal nocturnal dyspnea",
            "Pink or bloody sputum",
            "Crackles on auscultation",
            "Rapid heart rate",
            "Anxiety and sense of impending doom"
        ],
        "causes": [
            "Acute heart failure",
            "Left ventricular dysfunction",
            "Mitral stenosis",
            "High altitude pulmonary edema (HAPE)",
            "Sepsis",
            "Pneumonia",
            "Drug toxicity"
        ],
        "diagnosis": [
            "Chest X-ray (bilateral infiltrates, Kerley B lines)",
            "Echocardiogram",
            "BNP or NT-proBNP blood test",
            "ECG",
            "Blood gas analysis",
            "CT scan"
        ],
        "treatment": [
            "Oxygen therapy with positive pressure",
            "Diuretics",
            "Vasodilators",
            "Inotropic support",
            "Treatment of underlying cause",
            "Mechanical ventilation if severe"
        ],
        "xray_findings": "Bilateral infiltrates, Kerley B lines, bat wing or butterfly pattern"
    },
    
    "pneumoconiosis": {
        "name": "Pneumoconiosis",
        "category": "Occupational Lung Disease",
        "description": "Pneumoconiosis is a group of occupational lung diseases caused by chronic inhalation of mineral dusts, leading to pulmonary fibrosis.",
        "symptoms": [
            "Progressive shortness of breath",
            "Chronic cough",
            "Chest pain",
            "Fatigue",
            "Wheezing",
            "Reduced exercise tolerance"
        ],
        "causes": [
            "Asbestos exposure (asbestosis)",
            "Silica dust (silicosis)",
            "Coal dust (coal worker's pneumoconiosis)",
            "Other mineral dusts (talcosis, berylliosis)",
            "Prolonged occupational exposure"
        ],
        "prevention": [
            "Proper ventilation in workplace",
            "Use of respiratory protection",
            "Regular health screening",
            "Dust control measures",
            "Smoking cessation (worsens disease)"
        ],
        "treatment": [
            "Avoid further exposure",
            "Supportive care with oxygen",
            "Bronchodilators",
            "Corticosteroids (for some types)",
            "Treatment of complications"
        ]
    },
    
    "hypertension": {
        "name": "Hypertension (High Blood Pressure)",
        "category": "Cardiovascular Disease",
        "description": "Hypertension is persistently elevated blood pressure (≥130/80 mmHg), increasing risk of cardiovascular events and organ damage.",
        "symptoms": [
            "Often asymptomatic initially",
            "Headaches",
            "Shortness of breath",
            "Nosebleeds",
            "Visual disturbances",
            "Chest pain (in severe cases)"
        ],
        "causes": [
            "Primary hypertension (90-95% of cases, multifactorial)",
            "Secondary: kidney disease, adrenal disorders, sleep apnea",
            "Genetics",
            "Obesity",
            "Salt intake",
            "Stress and alcohol use"
        ],
        "risk_factors": [
            "Age over 60",
            "Family history",
            "Obesity",
            "Sedentary lifestyle",
            "High sodium diet",
            "Excessive alcohol"
        ],
        "treatment": [
            "Lifestyle modifications (diet, exercise, stress reduction)",
            "ACE inhibitors / ARBs",
            "Beta blockers",
            "Calcium channel blockers",
            "Diuretics",
            "Combination therapy for resistant hypertension"
        ],
        "prevention": [
            "Regular exercise (150 min/week)",
            "DASH diet (low sodium, high potassium)",
            "Weight management",
            "Stress management",
            "Limit alcohol"
        ]
    },
    
    "myocardial_infarction": {
        "name": "Myocardial Infarction (Heart Attack)",
        "category": "Acute Cardiovascular Emergency",
        "description": "Myocardial infarction is the death of heart muscle due to prolonged ischemia, typically caused by acute coronary artery occlusion.",
        "symptoms": [
            "Severe chest pain or pressure",
            "Shortness of breath",
            "Pain radiating to arm, neck, or jaw",
            "Nausea and vomiting",
            "Sweating (diaphoresis)",
            "Palpitations and anxiety",
            "Loss of consciousness"
        ],
        "causes": [
            "Atherosclerotic plaque rupture",
            "Coronary artery thrombosis",
            "Coronary vasospasm",
            "Coronary dissection",
            "Demand ischemia (supply-demand mismatch)"
        ],
        "risk_factors": [
            "Previous MI or angina",
            "Hypertension",
            "Diabetes",
            "Smoking",
            "High cholesterol",
            "Obesity",
            "Family history of early CAD"
        ],
        "diagnosis": [
            "EKG (ST elevation, T wave changes)",
            "Troponin elevation",
            "Other cardiac biomarkers (CK-MB, myoglobin)",
            "Echocardiogram",
            "Coronary angiography"
        ],
        "treatment": [
            "Emergency revascularization (PCI or fibrinolysis)",
            "Antiplatelet agents (aspirin, P2Y12 inhibitors)",
            "Anticoagulation (heparin)",
            "Beta blockers and ACE inhibitors",
            "Statins",
            "Cardiac rehabilitation"
        ]
    },
    
    "heart_failure": {
        "name": "Heart Failure",
        "category": "Cardiovascular Disease",
        "description": "Heart failure is a syndrome where the heart cannot pump sufficient blood to meet the body's metabolic needs, leading to fluid accumulation.",
        "symptoms": [
            "Shortness of breath at rest or with activity",
            "Fatigue and weakness",
            "Swelling in legs and ankles",
            "Rapid or pounding heartbeat",
            "Difficulty concentrating",
            "Persistent cough",
            "Orthopnea and paroxysmal nocturnal dyspnea"
        ],
        "causes": [
            "Previous myocardial infarction",
            "Hypertension",
            "Diabetes",
            "Cardiomyopathy",
            "Valvular heart disease",
            "Arrhythmias",
            "Myocarditis or pericarditis"
        ],
        "diagnosis": [
            "BNP or NT-proBNP elevation",
            "Echocardiography (LVEF measurement)",
            "Chest X-ray",
            "ECG",
            "Stress testing",
            "Cardiac catheterization"
        ],
        "treatment": [
            "ACE inhibitors / ARBs",
            "Beta blockers",
            "Diuretics",
            "Aldosterone antagonists",
            "ARNI (Sacubitril/valsartan)",
            "SGLT2 inhibitors",
            "Device therapy (ICD, CRT)",
            "Cardiac transplantation (in severe cases)"
        ]
    },
    
    "ischemic_heart_disease": {
        "name": "Ischemic Heart Disease",
        "category": "Cardiovascular Disease",
        "description": "Ischemic heart disease (coronary artery disease) results from reduced blood supply to the heart muscle due to coronary artery stenosis.",
        "symptoms": [
            "Angina (chest pain with exertion or stress)",
            "Shortness of breath",
            "Pain radiating to left arm or jaw",
            "Nausea",
            "Fatigue",
            "Anxiety",
            "Silent ischemia (asymptomatic in some patients)"
        ],
        "causes": [
            "Atherosclerotic plaque formation",
            "Endothelial dysfunction",
            "Coronary vasospasm",
            "Thrombosis",
            "Coronary embolism"
        ],
        "risk_factors": [
            "Hypertension",
            "High cholesterol",
            "Smoking",
            "Diabetes",
            "Obesity",
            "Physical inactivity",
            "Male gender or postmenopausal women"
        ],
        "diagnosis": [
            "EKG changes with ischemia",
            "Stress testing",
            "Coronary angiography (gold standard)",
            "CT angiography",
            "Troponin elevation in acute cases"
        ],
        "treatment": [
            "Antiplatelet agents (aspirin, P2Y12 inhibitors)",
            "Beta blockers",
            "ACE inhibitors",
            "Statins",
            "Nitrates for symptom relief",
            "PCI with stent or CABG",
            "Cardiac rehabilitation"
        ]
    },
    
    "malaria": {
        "name": "Malaria",
        "category": "Parasitic Infection",
        "description": "Malaria is a life-threatening disease caused by Plasmodium parasites transmitted by Anopheles mosquitoes, endemic in tropical and subtropical regions.",
        "symptoms": [
            "Fever and chills",
            "Headache",
            "Muscle and joint aches",
            "Fatigue and weakness",
            "Nausea and vomiting",
            "Jaundice (in severe cases)",
            "Organ failure (in severe malaria)"
        ],
        "causes": [
            "Plasmodium falciparum (most severe)",
            "Plasmodium vivax",
            "Plasmodium ovale",
            "Plasmodium malariae",
            "Plasmodium knowlesi",
            "Anopheles mosquito bite"
        ],
        "risk_factors": [
            "Living or traveling in endemic areas",
            "Pregnancy",
            "Child age (under 5 years)",
            "Low immunity",
            "Previous malaria episodes"
        ],
        "diagnosis": [
            "Blood smear microscopy (gold standard)",
            "Rapid diagnostic tests",
            "PCR testing",
            "Serological testing"
        ],
        "treatment": [
            "Artemisinin-based combination therapy (ACT)",
            "Quinine, doxycycline, clindamycin (alternatives)",
            "Supportive care",
            "Management of complications",
            "Anticonvulsants if cerebral malaria"
        ],
        "prevention": [
            "Insecticide-treated bed nets",
            "Indoor residual spraying",
            "Antimalarial prophylaxis in endemic areas",
            "Protective clothing and repellents"
        ]
    },
    
    "typhoid": {
        "name": "Typhoid Fever",
        "category": "Bacterial Infection",
        "description": "Typhoid fever is an acute, potentially life-threatening illness caused by Salmonella typhi, common in areas with poor sanitation.",
        "symptoms": [
            "Rising fever (up to 40-41°C)",
            "Headache",
            "Muscle aches",
            "Weakness and fatigue",
            "Abdominal pain",
            "Rose spots rash",
            "Delirium or coma (untreated)",
            "Diarrhea or constipation"
        ],
        "causes": [
            "Salmonella typhi infection",
            "Transmission via contaminated food/water",
            "Contact with infected person",
            "Poor hygiene and sanitation"
        ],
        "risk_factors": [
            "Travel to endemic areas",
            "Low socioeconomic status",
            "Poor sanitation",
            "Immunocompromised state"
        ],
        "diagnosis": [
            "Blood culture (gold standard, early stage)",
            "Stool culture (later stage)",
            "Typhidot assay",
            "Widal test (limited specificity)",
            "Complete blood count"
        ],
        "treatment": [
            "Fluoroquinolones (first-line, if susceptible)",
            "Cephalosporins (for resistant strains)",
            "Macrolides or azithromycin",
            "Supportive care and hydration",
            "Surgical intervention for perforation"
        ],
        "prevention": [
            "Typhoid vaccination",
            "Safe water and sanitation",
            "Good hygiene practices",
            "Safe food handling"
        ]
    },
    
    "dengue": {
        "name": "Dengue Fever",
        "category": "Viral Infection",
        "description": "Dengue is a mosquito-borne viral disease characterized by sudden onset of fever, characteristic body aches, rash, and potentially severe hemorrhagic manifestations.",
        "symptoms": [
            "Sudden fever (39-41°C)",
            "Severe headache and retro-orbital pain",
            "Myalgia and arthralgia (body aches)",
            "Rash (typically on day 3-4 of illness)",
            "Nausea and vomiting",
            "Bleeding (in hemorrhagic fever)",
            "Hypotension and shock (in severe cases)"
        ],
        "causes": [
            "Dengue virus serotypes 1-4",
            "Aedes aegypti mosquito transmission",
            "Less common: Aedes albopictus"
        ],
        "risk_factors": [
            "Living in or travel to dengue endemic areas",
            "Previous dengue infection",
            "Urban setting with high mosquito density"
        ],
        "diagnosis": [
            "NS1 antigen detection (early)",
            "IgM and IgG antibodies",
            "RT-PCR (quantitative viremia)",
            "Complete blood count (thrombocytopenia, hemoconcentration)"
        ],
        "treatment": [
            "Supportive care",
            "Fluid management and rehydration",
            "Acetaminophen (avoid NSAIDs)",
            "Blood transfusion if severe hemorrhage",
            "Monitoring for dengue shock syndrome"
        ],
        "prevention": [
            "Mosquito control (bed nets, insecticides)",
            "Dengue vaccine (in endemic areas)",
            "Protective clothing and repellents"
        ]
    },
    
    "hepatitis_b": {
        "name": "Hepatitis B",
        "category": "Viral Liver Disease",
        "description": "Hepatitis B is a viral infection causing inflammation of the liver, potentially leading to chronic liver disease, cirrhosis, and hepatocellular carcinoma.",
        "symptoms": [
            "Jaundice",
            "Abdominal pain",
            "Nausea and vomiting",
            "Fatigue",
            "Dark urine",
            "Pale stool",
            "Joint pain",
            "Fever"
        ],
        "causes": [
            "Hepatitis B virus (HBV) infection",
            "Transmission via blood, sexual contact, vertical transmission",
            "Percutaneous exposure"
        ],
        "risk_factors": [
            "Unprotected sexual contact",
            "Injection drug use",
            "Occupational exposure (healthcare workers)",
            "Birth to HBsAg-positive mother",
            "Shared personal items (toothbrush, razor)"
        ],
        "diagnosis": [
            "HBsAg (hepatitis B surface antigen)",
            "Anti-HBc (core antibody)",
            "Anti-HBs (surface antibody)",
            "HBeAg (e antigen), HBV DNA",
            "Liver function tests",
            "Liver biopsy (in some cases)"
        ],
        "treatment": [
            "Antiviral therapy (tenofovir, entecavir)",
            "Interferon-alpha",
            "Supportive care",
            "Monitoring for complications",
            "Treatment of cirrhosis if developed"
        ],
        "prevention": [
            "Hepatitis B vaccination",
            "Safe injection practices",
            "Safe sexual practices",
            "Screening of blood products"
        ]
    },
    
    "diabetes": {
        "name": "Diabetes Mellitus",
        "category": "Metabolic Disease",
        "description": "Diabetes is a chronic metabolic disease characterized by hyperglycemia, either from insufficient insulin production (Type 1) or insulin resistance (Type 2).",
        "symptoms": [
            "Increased thirst",
            "Frequent urination",
            "Fatigue and weakness",
            "Blurred vision",
            "Unexplained weight loss (Type 1)",
            "Tingling or numbness in extremities",
            "Slow-healing sores"
        ],
        "causes": [
            "Type 1: autoimmune destruction of pancreatic beta cells",
            "Type 2: insulin resistance and relative insulin deficiency",
            "Genetics and environmental factors",
            "Pancreatic disease or medication-induced"
        ],
        "risk_factors": [
            "Family history",
            "Obesity",
            "Physical inactivity",
            "Age",
            "Hypertension",
            "Pregnancy (gestational diabetes)"
        ],
        "diagnosis": [
            "Fasting blood glucose (≥126 mg/dL)",
            "Oral glucose tolerance test",
            "HbA1c (≥6.5%)",
            "Random blood glucose (≥200 mg/dL with symptoms)"
        ],
        "treatment": [
            "Lifestyle modification (diet, exercise, weight loss)",
            "Metformin (first-line for Type 2)",
            "Sulfonylureas and meglitinides",
            "Thiazolidinediones",
            "DPP-4 inhibitors and GLP-1 agonists",
            "SGLT2 inhibitors",
            "Insulin therapy"
        ],
        "prevention": [
            "Maintain healthy weight",
            "Regular physical activity",
            "Healthy diet (low glycemic index)",
            "Stress management",
            "Adequate sleep"
        ]
    },
    
    "obesity": {
        "name": "Obesity",
        "category": "Metabolic and Nutritional Disorder",
        "description": "Obesity is excessive body fat accumulation (BMI ≥30 kg/m²) associated with increased risk of multiple diseases and reduced life expectancy.",
        "symptoms": [
            "Excess body weight and fat",
            "Shortness of breath",
            "Joint pain",
            "Sleep apnea",
            "Fatigue",
            "Depression and anxiety",
            "Reduced mobility"
        ],
        "causes": [
            "Energy imbalance (excess intake, insufficient expenditure)",
            "Genetic predisposition",
            "Metabolic and endocrine disorders",
            "Medications (corticosteroids, antipsychotics)",
            "Psychological factors (emotional eating)"
        ],
        "risk_factors": [
            "Sedentary lifestyle",
            "High-calorie diet",
            "Low socioeconomic status",
            "Family history",
            "Age",
            "Medical conditions (hypothyroidism, PCOS)"
        ],
        "complications": [
            "Type 2 diabetes",
            "Hypertension",
            "Ischemic heart disease",
            "Stroke",
            "Sleep apnea",
            "Osteoarthritis",
            "Fatty liver disease",
            "Certain cancers"
        ],
        "treatment": [
            "Lifestyle modification (diet and exercise)",
            "Behavioral therapy",
            "Weight loss medications (GLP-1 agonists, orlistat)",
            "Bariatric surgery (in severe cases)"
        ]
    },
    
    "nephrolithiasis": {
        "name": "Kidney Stones (Nephrolithiasis)",
        "category": "Urological Condition",
        "description": "Kidney stones are hard mineral deposits that form in the kidneys, causing severe pain when passing through the urinary tract.",
        "symptoms": [
            "Severe flank pain",
            "Hematuria (blood in urine)",
            "Nausea and vomiting",
            "Frequent and painful urination",
            "Urinary urgency",
            "Fever (if infected)"
        ],
        "causes": [
            "Dehydration",
            "High dietary calcium, oxalate, uric acid",
            "Genetic factors",
            "Metabolic disorders (hyperparathyroidism)",
            "Urinary tract obstruction"
        ],
        "risk_factors": [
            "Male gender",
            "Age 30-50 years",
            "History of kidney stones",
            "Dehydration",
            "High protein diet",
            "Gout or hyperuricemia"
        ],
        "diagnosis": [
            "Non-contrast CT (gold standard)",
            "Ultrasound",
            "X-ray (for radiopaque stones)",
            "Urinalysis",
            "Urine culture"
        ],
        "treatment": [
            "Pain management",
            "Hydration and analgesia (conservative management)",
            "Extracorporeal shock wave lithotripsy (ESWL)",
            "Ureteroscopy with laser lithotripsy",
            "Percutaneous nephrolithotomy (for large stones)",
            "Antibiotics (if infected)"
        ],
        "prevention": [
            "Adequate hydration",
            "Dietary modifications",
            "Limit alcohol",
            "Medications (allopurinol, thiazide diuretics, citrate)"
        ]
    },
    
    "acutebronchiolitis": {
        "name": "Acute Bronchiolitis",
        "category": "Viral Respiratory Infection",
        "description": "Acute bronchiolitis is an acute viral infection affecting the small airways (bronchioles), most common in infants and young children.",
        "symptoms": [
            "Runny nose and nasal congestion",
            "Low-grade fever",
            "Rapid breathing (tachypnea)",
            "Wheezing and crackles",
            "Cough",
            "Retractions (use of accessory muscles)",
            "Poor feeding in severe cases"
        ],
        "causes": [
            "Respiratory syncytial virus (RSV, most common)",
            "Human metapneumovirus",
            "Parainfluenza virus",
            "Rhinovirus",
            "Influenza virus"
        ],
        "risk_factors": [
            "Age under 2 years",
            "Prematurity",
            "Chronic lung disease",
            "Congenital heart disease",
            "Immunodeficiency",
            "Secondhand smoke exposure"
        ],
        "diagnosis": [
            "Clinical presentation",
            "Chest X-ray (hyperinflation, atelectasis)",
            "Viral PCR test",
            "Pulse oximetry"
        ],
        "treatment": [
            "Supportive care (hydration, oxygen)",
            "Monitoring for respiratory failure",
            "Ribavirin (in severe cases)",
            "Corticosteroids (controversial, limited benefit)",
            "Bronchodilators (in some cases)",
            "Mechanical ventilation (severe cases)"
        ]
    },
    
    "influenza": {
        "name": "Influenza (Flu)",
        "category": "Viral Respiratory Infection",
        "description": "Influenza is contagious respiratory illness caused by influenza viruses, ranging from mild to severe with potential for serious complications.",
        "symptoms": [
            "Sudden onset fever (39-41°C)",
            "Dry cough",
            "Headache",
            "Myalgia and arthralgia",
            "Fatigue and weakness",
            "Sore throat",
            "Nasal congestion",
            "Nausea and vomiting (more common in children)"
        ],
        "causes": [
            "Influenza A virus",
            "Influenza B virus",
            "Influenza C virus (milder)",
            "Respiratory droplet transmission"
        ],
        "risk_factors": [
            "Age over 65 years",
            "Pregnancy",
            "Chronic medical conditions",
            "Immunocompromised status",
            "Healthcare worker status"
        ],
        "diagnosis": [
            "RT-PCR (most reliable)",
            "Rapid antigen test",
            "Viral culture",
            "Symptoms during flu season"
        ],
        "treatment": [
            "Antivirals (oseltamivir, zanamivir, peramivir): most effective within 48 hours",
            "Symptomatic treatment (antipyretics, analgesics)",
            "Rest and hydration",
            "Management of complications"
        ],
        "prevention": [
            "Annual influenza vaccination",
            "Hand hygiene",
            "Respiratory etiquette",
            "Isolation of sick individuals",
            "Antivirals for high-risk contacts"
        ]
    },
    
    "glomerulonephritis": {
        "name": "Glomerulonephritis",
        "category": "Kidney Disease",
        "description": "Glomerulonephritis is inflammation of the kidney glomeruli, causing hematuria, proteinuria, and potential progression to renal failure.",
        "symptoms": [
            "Blood in urine (hematuria)",
            "Cola or tea-colored urine",
            "Edema (swelling of face and legs)",
            "Hypertension",
            "Reduced urine output",
            "Fatigue",
            "Respiratory difficulty (if pulmonary edema)"
        ],
        "causes": [
            "Post-infectious: streptococcal pharyngitis, endocarditis",
            "Autoimmune: lupus, vasculitis",
            "Primary: IgA nephropathy, membranoproliferative",
            "Secondary: hepatitis B/C, diabetes"
        ],
        "diagnosis": [
            "Urinalysis (proteinuria, hematuria, casts)",
            "Serum creatinine and BUN",
            "Renal function tests",
            "Serologic tests (ANA, ANCA, anti-GBM)",
            "Kidney biopsy (if necessary)"
        ],
        "treatment": [
            "Treat underlying cause",
            "ACE inhibitors / ARBs",
            "Corticosteroids (in some cases)",
            "Immunosuppressive agents",
            "Diuretics for edema",
            "Blood pressure control",
            "Dialysis and transplantation (if chronic kidney disease develops)"
        ]
    },
    
    "uti": {
        "name": "Urinary Tract Infection (UTI)",
        "category": "Bacterial Infection",
        "description": "UTI is a bacterial infection of any part of the urinary system (urethra, bladder, ureters, kidneys), ranging from uncomplicated cystitis to pyelonephritis.",
        "symptoms": [
            "Dysuria (painful urination)",
            "Frequency and urgency",
            "Suprapubic pain",
            "Hematuria",
            "Fever (in pyelonephritis)",
            "Flank pain and nausea (in pyelonephritis)",
            "Sepsis signs (in complicated UTI)"
        ],
        "causes": [
            "Escherichia coli (most common)",
            "Staphylococcus saprophyticus",
            "Proteus, Klebsiella, Enterococcus",
            "Ascending infection from urethra"
        ],
        "risk_factors": [
            "Female gender",
            "Sexual activity",
            "Urinary catheterization",
            "Pregnancy",
            "Urinary tract obstruction",
            "Neurogenic bladder"
        ],
        "diagnosis": [
            "Urinalysis (pyuria, bacteriuria)",
            "Urine culture (gold standard)",
            "Nitrites and leukocyte esterase",
            "Imaging (ultrasound, CT) for complicated cases"
        ],
        "treatment": [
            "Antibiotics: fluoroquinolones, trimethoprim-sulfamethoxazole, nitrofurantoin",
            "Hydration",
            "Analgesics",
            "Urinary alkalinization (optional)",
            "Treatment of complications and underlying causes"
        ],
        "prevention": [
            "Hydration",
            "Frequent micturition",
            "Urinary hygiene",
            "Sexual hygiene",
            "Avoid irritants"
        ]
    },
    
    "appendicitis": {
        "name": "Acute Appendicitis",
        "category": "Acute Abdominal Condition",
        "description": "Acute appendicitis is inflammation of the appendix, requiring emergency surgical intervention to prevent perforation and sepsis.",
        "symptoms": [
            "Abdominal pain starting periumbilically, localizing to RLQ",
            "Anorexia, nausea and vomiting",
            "Fever",
            "Rebound tenderness at McBurney's point",
            "Guarding and rigidity (if perforated)",
            "Constipation or diarrhea"
        ],
        "causes": [
            "Luminal obstruction (fecalith, lymphoid hyperplasia)",
            "Bacterial invasion of appendiceal wall",
            "Development of inflammation and suppuration"
        ],
        "diagnosis": [
            "Clinical examination (McBurney's point tenderness)",
            "Ultrasound (appendiceal diameter >6mm)",
            "CT scan (gold standard, high sensitivity/specificity)",
            "Laboratory: elevated WBC, left shift",
            "Doppler ultrasound"
        ],
        "treatment": [
            "Emergency appendectomy (open or laparoscopic)",
            "Preoperative fluid resuscitation",
            "Antibiotics (cefoxitin or cephalosporin + metronidazole)",
            "Analgesia",
            "Management of complications (perforation, sepsis)"
        ]
    },
    
    "gastroenteritis": {
        "name": "Acute Gastroenteritis",
        "category": "Gastrointestinal Infection",
        "description": "Acute gastroenteritis is inflammation of the stomach and intestines, usually viral or bacterial, causing acute diarrhea and vomiting.",
        "symptoms": [
            "Nausea and vomiting",
            "Diarrhea (watery or bloody)",
            "Abdominal cramps",
            "Fever",
            "Malaise and fatigue",
            "Dehydration signs",
            "Loss of appetite"
        ],
        "causes": [
            "Viral: rotavirus, norovirus, enteroviruses",
            "Bacterial: Salmonella, Shigella, E. coli, Campylobacter, Vibrio cholera",
            "Parasitic: Giardia, Entamoeba",
            "Toxin-mediated: S. aureus enterotoxin, Clostridium difficile"
        ],
        "diagnosis": [
            "Clinical presentation",
            "Stool culture (bacterial)",
            "Stool antigen or PCR (viral)",
            "Stool microscopy (parasitic)",
            "Blood cultures (if bacteremia suspected)"
        ],
        "treatment": [
            "Oral rehydration solution (first-line)",
            "IV fluid replacement (severe dehydration)",
            "Antiemetics",
            "Antimotility agents (avoid in bloody diarrhea)",
            "Antibiotics (selected cases)",
            "Supportive care"
        ],
        "prevention": [
            "Handwashing and sanitation",
            "Safe food preparation",
            "Vaccination (rotavirus)",
            "Clean water",
            "Cholera vaccine (in endemic areas)"
        ]
    },
    
    "peptic_ulcer_disease": {
        "name": "Peptic Ulcer Disease",
        "category": "Gastrointestinal Disease",
        "description": "Peptic ulcer disease involves mucosal defects in the stomach or duodenum, commonly caused by Helicobacter pylori infection or NSAID use.",
        "symptoms": [
            "Epigastric pain (burning or gnawing)",
            "Pain relief with food or antacids",
            "Nausea",
            "Vomiting (sometimes bloody)",
            "Black tarry stools (melena)",
            "Weight loss",
            "Feeling of fullness"
        ],
        "causes": [
            "Helicobacter pylori infection (60% of cases)",
            "NSAIDs (30% of cases)",
            "Zollinger-Ellison syndrome",
            "Stress ulcers (severe illness)",
            "Malignancy"
        ],
        "diagnosis": [
            "Upper gastrointestinal endoscopy (EGD, gold standard)",
            "Biopsy (for H. pylori, malignancy)",
            "H. pylori testing (breath, stool, serology, endoscopy)",
            "CT scan (for complications)"
        ],
        "treatment": [
            "H. pylori eradication (triple or quadruple therapy)",
            "Proton pump inhibitors",
            "H2 receptor antagonists",
            "Sucralfate",
            "Avoid NSAIDs and alcohol",
            "Endoscopic hemostasis (for bleeding)",
            "Surgery (for perforation or obstruction)"
        ]
    },
    
    "cirrhosis": {
        "name": "Liver Cirrhosis",
        "category": "Chronic Liver Disease",
        "description": "Cirrhosis is advanced chronic liver disease with irreversible fibrosis and nodule formation, leading to portal hypertension and end-stage liver failure.",
        "symptoms": [
            "Jaundice",
            "Ascites (abdominal swelling)",
            "Portal hypertension (varices, splenomegaly)",
            "Hepatic encephalopathy (confusion, altered mental status)",
            "Coagulopathy (easy bruising)",
            "Fatigue and weakness",
            "Variceal bleeding"
        ],
        "causes": [
            "Chronic hepatitis B or C",
            "Alcoholic liver disease",
            "Nonalcoholic fatty liver disease (NAFLD)",
            "Autoimmune hepatitis",
            "Primary biliary cholangitis (PBC)",
            "Primary sclerosing cholangitis (PSC)",
            "Hemochromatosis, Wilson disease"
        ],
        "diagnosis": [
            "Clinical and laboratory findings",
            "Elevated liver enzymes (ALT, AST, GGT, ALP)",
            "Prolonged PT/INR (coagulopathy)",
            "Hypoalbuminemia",
            "Liver biopsy (definitive)",
            "Ultrasound or CT (imaging)"
        ],
        "treatment": [
            "Treat underlying cause",
            "Management of complications (ascites, encephalopathy, bleeding)",
            "Beta blockers (portal hypertension)",
            "Diuretics and sodium restriction",
            "Lactulose and rifaxomicin (encephalopathy)",
            "FFP and platelet transfusions",
            "Liver transplantation (definitive)"
        ]
    }
}


def get_disease_info(disease_name: str) -> dict:
    """Get comprehensive information about a disease"""
    disease_key = disease_name.lower().replace(" ", "_").replace("-", "")
    return MEDICAL_KNOWLEDGE.get(disease_key, {})


def search_symptoms(symptom: str) -> list:
    """Search for diseases matching a symptom"""
    symptom = symptom.lower()
    matching_diseases = []
    
    for disease_key, disease_info in MEDICAL_KNOWLEDGE.items():
        symptoms = disease_info.get("symptoms", [])
        if any(symptom in s.lower() for s in symptoms):
            matching_diseases.append({
                "disease": disease_info.get("name"),
                "category": disease_info.get("category"),
                "description": disease_info.get("description")
            })
    
    return matching_diseases


def get_all_diseases() -> list:
    """Get list of all diseases in the knowledge base"""
    return [info.get("name") for info in MEDICAL_KNOWLEDGE.values() if "name" in info]
