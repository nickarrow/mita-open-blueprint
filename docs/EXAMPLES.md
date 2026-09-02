# MITA Data Usage Examples

This document provides practical examples for working with MITA BCM and BPT JSON data.

## Fetching Data from GitHub (Recommended)

### Python: Load from GitHub URL

```python
import json
import urllib.request

# Base URL for raw GitHub content
BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data"

def load_from_github(file_path):
    """Load JSON file directly from GitHub."""
    url = f"{BASE_URL}/{file_path}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

# Load a BCM file
bcm = load_from_github("bcm/care_management/CM_Establish_Case_BCM_v3.0.json")
print(f"Process: {bcm['process_name']}")
print(f"Questions: {len(bcm['maturity_model']['capability_questions'])}")

# Load a BPT file
bpt = load_from_github("bpt/care_management/CM_Establish_Case_BPT_v3.0.json")
print(f"Process: {bpt['process_name']}")
print(f"Steps: {len(bpt['process_details']['process_steps'])}")
```

### Python: Using requests library

```python
import json
import requests

BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data"

def load_from_github(file_path):
    """Load JSON file from GitHub using requests."""
    url = f"{BASE_URL}/{file_path}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Load and use
bcm = load_from_github("bcm/care_management/CM_Establish_Case_BCM_v3.0.json")
```

### JavaScript/Node.js: Fetch from GitHub

```javascript
const BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data";

async function loadFromGitHub(filePath) {
    const url = `${BASE_URL}/${filePath}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Load a BCM file
const bcm = await loadFromGitHub("bcm/care_management/CM_Establish_Case_BCM_v3.0.json");
console.log(`Process: ${bcm.process_name}`);
console.log(`Questions: ${bcm.maturity_model.capability_questions.length}`);

// Load a BPT file
const bpt = await loadFromGitHub("bpt/care_management/CM_Establish_Case_BPT_v3.0.json");
console.log(`Process: ${bpt.process_name}`);
console.log(`Steps: ${bpt.process_details.process_steps.length}`);
```

### Browser JavaScript: Fetch from GitHub

```html
<!DOCTYPE html>
<html>
<head>
    <title>MITA Data Viewer</title>
</head>
<body>
    <div id="output"></div>
    
    <script>
        const BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data";
        
        async function loadAndDisplay() {
            const bcm = await fetch(`${BASE_URL}/bcm/care_management/CM_Establish_Case_BCM_v3.0.json`)
                .then(r => r.json());
            
            document.getElementById('output').innerHTML = `
                <h2>${bcm.process_name}</h2>
                <p>Business Area: ${bcm.business_area}</p>
                <p>Questions: ${bcm.maturity_model.capability_questions.length}</p>
            `;
        }
        
        loadAndDisplay();
    </script>
</body>
</html>
```

## Basic File Loading (Local Development)

If you've cloned the repository locally:

### Load a Single BCM File

```python
import json

# Load a Business Capability Model
with open('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json') as f:
    bcm = json.load(f)

print(f"Process: {bcm['process_name']}")
print(f"Business Area: {bcm['business_area']}")
print(f"Questions: {len(bcm['maturity_model']['capability_questions'])}")
```

### Load a Single BPT File

```python
import json

# Load a Business Process Template
with open('data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json') as f:
    bpt = json.load(f)

print(f"Process: {bpt['process_name']}")
print(f"Steps: {len(bpt['process_details']['process_steps'])}")

# trigger_events is an object with two arrays, not a flat list
triggers = bpt['process_details']['trigger_events']
print(f"Environment-based triggers: {len(triggers['environment_based'])}")
print(f"Interaction-based triggers: {len(triggers['interaction_based'])}")
```

## Working with BCM Data

### Extract All Questions from a BCM

```python
import json

with open('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json') as f:
    bcm = json.load(f)

for i, q in enumerate(bcm['maturity_model']['capability_questions'], 1):
    print(f"\nQuestion {i}: {q['question']}")
    print(f"Category: {q['category']}")
```

### Compare Maturity Levels

```python
import json

with open('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json') as f:
    bcm = json.load(f)

# Get first question
question = bcm['maturity_model']['capability_questions'][0]

print(f"Question: {question['question']}\n")
for level in range(1, 6):
    print(f"Level {level}:")
    print(f"  {question['levels'][f'level_{level}']}\n")
```

### Find Questions by Category

```python
import json

def find_questions_by_category(bcm_file, category_keyword):
    with open(bcm_file) as f:
        bcm = json.load(f)
    
    matching = []
    for q in bcm['maturity_model']['capability_questions']:
        if category_keyword.lower() in q['category'].lower():
            matching.append(q)
    
    return matching

# Find all "Timeliness" questions
timeliness_qs = find_questions_by_category(
    'data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json',
    'Timeliness'
)

for q in timeliness_qs:
    print(f"- {q['question']}")
```

## Working with BPT Data

### List All Process Steps

```python
import json

with open('data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json') as f:
    bpt = json.load(f)

print(f"Process: {bpt['process_name']}\n")
print("Steps:")
for step in bpt['process_details']['process_steps']:
    print(f"  {step}")
```

### Extract Trigger Events and Results

```python
import json

with open('data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json') as f:
    bpt = json.load(f)

# trigger_events is an object with two categorised arrays
triggers = bpt['process_details']['trigger_events']

print("Environment-based triggers (schedules, timers, system conditions):")
for trigger in triggers['environment_based']:
    print(f"  • {trigger}")

print("\nInteraction-based triggers (input from people or other processes):")
for trigger in triggers['interaction_based']:
    print(f"  • {trigger}")

print("\nExpected Results:")
for result in bpt['process_details']['results']:
    print(f"  • {result}")
```

### Find Process Dependencies

```python
import json

def get_process_dependencies(bpt_file):
    with open(bpt_file) as f:
        bpt = json.load(f)
    
    return {
        'process': bpt['process_name'],
        'predecessors': bpt['process_details'].get('predecessor_processes', []),
        'successors': bpt['process_details'].get('successor_processes', [])
    }

deps = get_process_dependencies(
    'data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json'
)

print(f"Process: {deps['process']}")
print(f"\nComes After: {', '.join(deps['predecessors']) if deps['predecessors'] else 'None'}")
print(f"Comes Before: {', '.join(deps['successors']) if deps['successors'] else 'None'}")
```

## Cross-File Analysis

### Load All Files in a Business Area from GitHub

```python
import json
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/nickarrow/mita-open-blueprint/main/data"

# List of Care Management BCM files (you can maintain this list or fetch from GitHub API)
CARE_MANAGEMENT_BCMS = [
    "CM_Authorize_Referral_BCM_v3.0.json",
    "CM_Authorize_Service_BCM_v3.0.json",
    "CM_Authorize_Treatment_Plan_BCM_v3.0.json",
    "CM_Establish_Case_BCM_v3.0.json",
    "CM_Manage_Case_Information_BCM_v3.0.json",
    "CM_Manage_Population_Health_Outreach_BCM_v3.0.json",
    "CM_Manage_Registry_BCM_v3.0.json",
    "CM_Manage_Treatment_Plan_and_Outcomes_BCM_v3.0.json",
    "CM_Perform_Screening_and_Assessment_BCM_v3.0.json"
]

def load_business_area_from_github(area_name, file_list, doc_type='bcm'):
    """Load all files in a business area from GitHub."""
    files = {}
    
    for filename in file_list:
        url = f"{BASE_URL}/{doc_type}/{area_name}/{filename}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            files[filename.replace('.json', '')] = data
    
    return files

# Load all Care Management BCMs
care_bcms = load_business_area_from_github('care_management', CARE_MANAGEMENT_BCMS, 'bcm')
print(f"Loaded {len(care_bcms)} Care Management BCM files")

for filename, data in care_bcms.items():
    print(f"  - {data['process_name']}")
```

### Load All Files in a Business Area (Local)

```python
import json
from pathlib import Path

def load_business_area(area_name, doc_type='bcm'):
    area_path = Path(f'data/{doc_type}/{area_name}')
    files = {}
    
    for json_file in area_path.glob('*.json'):
        with open(json_file) as f:
            files[json_file.stem] = json.load(f)
    
    return files

# Load all Care Management BCMs
care_bcms = load_business_area('care_management', 'bcm')
print(f"Loaded {len(care_bcms)} Care Management BCM files")

for filename, data in care_bcms.items():
    print(f"  - {data['process_name']}")
```

### Pair BCM with BPT — use `process_id`, not the filename

**Join on `process_id`.** It is identical for a BCM/BPT pair and is insensitive
to naming. `process_name` and the filename stem also pair correctly — all three
give 76 pairs.

Two processes are named inconsistently by CMS: Appendix D spells them
`Manage Treatment Plan**s** and Outcomes` and `**Maintain** Reference
Information`, while Appendix C and the framework's process index use
`Manage Treatment Plan and Outcomes` and `Manage Reference Information`. The
dataset follows the index so pairing works, and keeps the Appendix D wording in
`metadata.source_process_name`. Before that was reconciled, a name-based join
quietly returned 74 pairs instead of 76.

```python
import json
from pathlib import Path

def build_index(root='data'):
    """Index every record by process_id, giving {id: {'bcm': ..., 'bpt': ...}}."""
    index = {}
    for path in Path(root).rglob('*.json'):
        with open(path, encoding='utf-8') as fh:
            record = json.load(fh)
        entry = index.setdefault(record['process_id'], {})
        entry[record['document_type'].lower()] = record
    return index

index = build_index()
print(f"Processes: {len(index)}")
print(f"Complete pairs: {sum(1 for v in index.values() if 'bcm' in v and 'bpt' in v)}")

pair = index['CM_ESTABLISH_CASE']
print(f"\nProcess: {pair['bpt']['process_name']}")
print(f"BCM questions: {len(pair['bcm']['maturity_model']['capability_questions'])}")
print(f"BPT steps: {len(pair['bpt']['process_details']['process_steps'])}")

# the pair CMS spells two ways
divergent = index['CM_MANAGE_TREATMENT_PLAN_AND_OUTCOMES']
print(f"\nBPT name: {divergent['bpt']['process_name']}")
print(f"BCM name: {divergent['bcm']['process_name']}")
```

### Trace any value back to its source

Every record carries the PDF and page range it came from, so any claim can be
checked against the original CMS document.

```python
import json

with open('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json', encoding='utf-8') as fh:
    bcm = json.load(fh)

meta = bcm['metadata']
print(f"{bcm['process_id']} came from:")
print(f"  {meta['source_file']}, pages {meta['source_page_range']}")
```

### Count Questions Across All BCMs

```python
import json
from pathlib import Path

total_questions = 0
total_levels = 0

for bcm_file in Path('data/bcm').rglob('*.json'):
    with open(bcm_file) as f:
        bcm = json.load(f)
    
    num_questions = len(bcm['maturity_model']['capability_questions'])
    total_questions += num_questions
    total_levels += num_questions * 5  # 5 levels per question

print(f"Total BCM Questions: {total_questions}")
print(f"Total Maturity Levels: {total_levels}")
```

## Search and Filter

### Find Processes by Keyword

```python
import json
from pathlib import Path

def search_processes(keyword, doc_type='bpt'):
    results = []
    
    for json_file in Path(f'data/{doc_type}').rglob('*.json'):
        with open(json_file) as f:
            data = json.load(f)
        
        # Search in process name and description
        if doc_type == 'bpt':
            searchable = data['process_name'] + ' ' + data['process_details']['description']
        else:
            searchable = data['process_name']
        
        if keyword.lower() in searchable.lower():
            results.append({
                'file': str(json_file),
                'process': data['process_name'],
                'area': data['business_area']
            })
    
    return results

# Find all processes related to "enrollment"
enrollment_processes = search_processes('enrollment')

print(f"Found {len(enrollment_processes)} processes:")
for p in enrollment_processes:
    print(f"  - {p['process']} ({p['area']})")
```

### Filter by Process Code

```python
import json
from pathlib import Path

def get_processes_by_code(process_code, doc_type='bcm'):
    processes = []
    
    for json_file in Path(f'data/{doc_type}').rglob(f'{process_code}_*.json'):
        with open(json_file) as f:
            data = json.load(f)
        
        processes.append({
            'name': data['process_name'],
            'code': data['process_code'],
            'area': data['business_area'],
            'file': str(json_file)
        })
    
    return processes

# Get all Care Management (CM) processes
cm_processes = get_processes_by_code('CM', 'bcm')

print(f"Care Management Processes ({len(cm_processes)}):")
for p in cm_processes:
    print(f"  - {p['name']}")
```

## Generating Reports

### Create Maturity Assessment Report

```python
import json

def generate_maturity_report(bcm_file):
    with open(bcm_file) as f:
        bcm = json.load(f)
    
    print(f"MATURITY ASSESSMENT: {bcm['process_name']}")
    print(f"Business Area: {bcm['business_area']}")
    print(f"=" * 60)
    
    for i, q in enumerate(bcm['maturity_model']['capability_questions'], 1):
        print(f"\n{i}. {q['question']}")
        print(f"   Category: {q['category']}")
        print(f"\n   Maturity Levels:")
        for level in range(1, 6):
            print(f"   [{level}] {q['levels'][f'level_{level}'][:80]}...")

generate_maturity_report('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json')
```

### Create Process Flow Report

```python
import json

def generate_process_report(bpt_file):
    with open(bpt_file) as f:
        bpt = json.load(f)
    
    print(f"PROCESS: {bpt['process_name']}")
    print(f"Business Area: {bpt['business_area']}")
    print(f"=" * 60)
    
    print(f"\nDESCRIPTION:")
    print(bpt['process_details']['description'][:200] + "...")
    
    print(f"\nTRIGGER EVENTS:")
    for kind, triggers in bpt['process_details']['trigger_events'].items():
        print(f"  {kind}:")
        for trigger in triggers:
            print(f"    • {trigger}")
    
    print(f"\nPROCESS STEPS:")
    for step in bpt['process_details']['process_steps']:
        print(f"  {step}")
    
    print(f"\nEXPECTED RESULTS:")
    for result in bpt['process_details']['results']:
        print(f"  • {result}")

generate_process_report('data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json')
```

## Building Applications

### Simple Maturity Assessment Tool

```python
import json

class MaturityAssessment:
    def __init__(self, bcm_file):
        with open(bcm_file) as f:
            self.bcm = json.load(f)
        self.responses = {}
    
    def ask_questions(self):
        questions = self.bcm['maturity_model']['capability_questions']
        
        for i, q in enumerate(questions):
            print(f"\n{i+1}. {q['question']}")
            print("\nMaturity Levels:")
            for level in range(1, 6):
                print(f"  {level}. {q['levels'][f'level_{level}'][:60]}...")
            
            response = input("\nYour current level (1-5): ")
            self.responses[i] = int(response)
    
    def calculate_score(self):
        if not self.responses:
            return 0
        return sum(self.responses.values()) / len(self.responses)
    
    def generate_report(self):
        avg_score = self.calculate_score()
        print(f"\n{'='*60}")
        print(f"MATURITY ASSESSMENT RESULTS")
        print(f"Process: {self.bcm['process_name']}")
        print(f"Average Maturity Level: {avg_score:.2f}")
        print(f"{'='*60}")

# Usage
# assessment = MaturityAssessment('data/bcm/care_management/CM_Establish_Case_BCM_v3.0.json')
# assessment.ask_questions()
# assessment.generate_report()
```

### Process Workflow Viewer

```python
import json

class ProcessViewer:
    def __init__(self, bpt_file):
        with open(bpt_file) as f:
            self.bpt = json.load(f)
    
    def display(self):
        print(f"\n{'='*60}")
        print(f"PROCESS: {self.bpt['process_name']}")
        print(f"{'='*60}")
        
        print(f"\n📋 DESCRIPTION:")
        print(f"{self.bpt['process_details']['description']}\n")
        
        print(f"⚡ TRIGGER EVENTS:")
        for trigger in (self.bpt['process_details']['trigger_events']['environment_based']
                        + self.bpt['process_details']['trigger_events']['interaction_based']):
            print(f"  • {trigger}")
        
        print(f"\n📝 PROCESS STEPS:")
        for i, step in enumerate(self.bpt['process_details']['process_steps'], 1):
            print(f"  {i}. {step}")
        
        print(f"\n✅ EXPECTED RESULTS:")
        for result in self.bpt['process_details']['results']:
            print(f"  • {result}")
        
        if self.bpt['process_details'].get('predecessor_processes'):
            print(f"\n⬅️  COMES AFTER:")
            for pred in self.bpt['process_details']['predecessor_processes']:
                print(f"  • {pred}")
        
        if self.bpt['process_details'].get('successor_processes'):
            print(f"\n➡️  COMES BEFORE:")
            for succ in self.bpt['process_details']['successor_processes']:
                print(f"  • {succ}")

# Usage
viewer = ProcessViewer('data/bpt/care_management/CM_Establish_Case_BPT_v3.0.json')
viewer.display()
```

## More Examples

For more advanced usage:
- See the validation scripts in `tools/`
- Check the conversion methodology in `docs/CONVERSION_METHODOLOGY.md`
- Explore the data structure reference in `docs/DATA_STRUCTURE.md`

## Contributing Examples

Have a useful example? Please contribute it via Pull Request!
