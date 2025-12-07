"""
Skill Tree Generator
Extracts skills from a resume PDF and creates an interactive skill tree visualization.
Uses xAI API to analyze and structure skills hierarchically.
"""

import os
import json
import requests
from typing import Dict, List, Any

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class SkillTreeGenerator:
    def __init__(self, api_key: str = None):
        """Initialize the skill tree generator."""
        self.api_key = api_key or os.getenv('XAI_API_KEY')
        self.api_url = "https://api.x.ai/v1/chat/completions"
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF resume."""
        text = ""
        
        if pdfplumber is None and PyPDF2 is None:
            raise ImportError("Please install required packages: pip install -r requirements.txt")
        
        # Try pdfplumber first (better for complex layouts)
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"pdfplumber failed, trying PyPDF2: {e}")
        
        # Fallback to PyPDF2
        if not text and PyPDF2:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                print(f"PyPDF2 also failed: {e2}")
        
        if not text:
            raise Exception("Could not extract text from PDF. Please ensure the PDF is not encrypted or corrupted.")
        
        return text.strip()
    
    def analyze_resume_with_xai(self, resume_text: str) -> Dict[str, Any]:
        """Use xAI API to analyze resume and extract structured skill information."""
        
        prompt = f"""Analyze the following resume and extract all skills, organizing them into a hierarchical skill tree structure.

Resume:
{resume_text}

Please identify:
1. Core technical skills (programming languages, frameworks, tools)
2. Soft skills (communication, leadership, etc.)
3. Domain expertise (AI/ML, web development, etc.)
4. Certifications and qualifications
5. Years of experience or proficiency levels where mentioned

Return a JSON structure with this format:
{{
    "skills": {{
        "technical": {{
            "programming_languages": ["skill1", "skill2"],
            "frameworks": ["skill1", "skill2"],
            "tools": ["skill1", "skill2"],
            "databases": ["skill1", "skill2"],
            "cloud_platforms": ["skill1", "skill2"]
        }},
        "soft_skills": ["skill1", "skill2"],
        "domains": ["domain1", "domain2"],
        "certifications": ["cert1", "cert2"]
    }},
    "experience_levels": {{
        "skill_name": "beginner|intermediate|advanced|expert"
    }},
    "skill_relationships": [
        {{"parent": "parent_skill", "child": "child_skill", "type": "prerequisite|related|specialization"}}
    ]
}}

Only return valid JSON, no additional text."""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert resume analyzer. Extract skills and create a structured skill tree. Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4-latest",
            "stream": False,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Extract the JSON from the response
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Try to parse JSON from the content
            # Sometimes the API wraps it in markdown code blocks
            content = content.strip()
            if content.startswith('```'):
                # Remove markdown code blocks
                lines = content.split('\n')
                content = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            
            skill_data = json.loads(content)
            return skill_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response content: {content[:500]}")
            # Return a fallback structure
            return self._fallback_skill_extraction(resume_text)
        except Exception as e:
            print(f"Error calling xAI API: {e}")
            return self._fallback_skill_extraction(resume_text)
    
    def _fallback_skill_extraction(self, resume_text: str) -> Dict[str, Any]:
        """Fallback skill extraction using keyword matching if API fails."""
        # Common technical skills to look for
        tech_keywords = {
            'programming_languages': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'TypeScript', 'SQL', 'R', 'Swift', 'Kotlin'],
            'frameworks': ['React', 'Vue', 'Angular', 'Django', 'Flask', 'FastAPI', 'Spring', 'Node.js', 'Express', 'TensorFlow', 'PyTorch'],
            'tools': ['Git', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Jenkins', 'CI/CD', 'Linux', 'MongoDB', 'PostgreSQL', 'Redis']
        }
        
        found_skills = {'programming_languages': [], 'frameworks': [], 'tools': []}
        
        resume_lower = resume_text.lower()
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword.lower() in resume_lower:
                    found_skills[category].append(keyword)
        
        return {
            "skills": {
                "technical": found_skills,
                "soft_skills": [],
                "domains": [],
                "certifications": []
            },
            "experience_levels": {},
            "skill_relationships": []
        }
    
    def build_skill_tree(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a hierarchical skill tree structure."""
        
        tree = {
            "name": "Skills",
            "children": []
        }
        
        # Add technical skills
        if "technical" in skill_data.get("skills", {}):
            tech_skills = skill_data["skills"]["technical"]
            tech_node = {
                "name": "Technical Skills",
                "children": []
            }
            
            for category, skills in tech_skills.items():
                if skills:
                    category_node = {
                        "name": category.replace("_", " ").title(),
                        "children": [{"name": skill, "type": "skill"} for skill in skills]
                    }
                    tech_node["children"].append(category_node)
            
            if tech_node["children"]:
                tree["children"].append(tech_node)
        
        # Add soft skills
        if skill_data.get("skills", {}).get("soft_skills"):
            soft_node = {
                "name": "Soft Skills",
                "children": [{"name": skill, "type": "skill"} for skill in skill_data["skills"]["soft_skills"]]
            }
            tree["children"].append(soft_node)
        
        # Add domains
        if skill_data.get("skills", {}).get("domains"):
            domain_node = {
                "name": "Domain Expertise",
                "children": [{"name": domain, "type": "skill"} for domain in skill_data["skills"]["domains"]]
            }
            tree["children"].append(domain_node)
        
        # Add certifications
        if skill_data.get("skills", {}).get("certifications"):
            cert_node = {
                "name": "Certifications",
                "children": [{"name": cert, "type": "certification"} for cert in skill_data["skills"]["certifications"]]
            }
            tree["children"].append(cert_node)
        
        return tree
    
    def generate_skill_tree(self, pdf_path: str, output_json: str = "skill_tree.json", output_html: str = "skill_tree.html"):
        """Main method to generate skill tree from resume PDF."""
        print(f"Extracting text from {pdf_path}...")
        resume_text = self.extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(resume_text)} characters from PDF")
        
        if self.api_key:
            print("Analyzing resume with xAI API...")
            skill_data = self.analyze_resume_with_xai(resume_text)
        else:
            print("No API key found, using fallback extraction...")
            skill_data = self._fallback_skill_extraction(resume_text)
        
        print("Building skill tree structure...")
        skill_tree = self.build_skill_tree(skill_data)
        
        # Save JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(skill_tree, f, indent=2, ensure_ascii=False)
        print(f"Saved skill tree JSON to {output_json}")
        
        # Generate HTML visualization
        self.generate_html_visualization(skill_tree, output_html)
        print(f"Generated HTML visualization: {output_html}")
        
        return skill_tree
    
    def generate_html_visualization(self, skill_tree: Dict[str, Any], output_path: str):
        """Generate an interactive HTML visualization of the skill tree."""
        
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skill Tree Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .skill-tree {
            width: 100%;
            height: 800px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: auto;
        }
        .node circle {
            fill: #fff;
            stroke: #667eea;
            stroke-width: 3px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .node circle:hover {
            stroke-width: 5px;
            fill: #f0f0ff;
        }
        .node--internal circle {
            fill: #764ba2;
            stroke: #667eea;
        }
        .node--leaf circle {
            fill: #4CAF50;
            stroke: #45a049;
        }
        .node--certification circle {
            fill: #FF9800;
            stroke: #F57C00;
        }
        .node text {
            font: 14px sans-serif;
            font-weight: 500;
            pointer-events: none;
        }
        .link {
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
        }
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        button:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌳 Skill Tree Visualization</h1>
        <div class="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetZoom()">Reset</button>
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>
        <div class="skill-tree" id="skill-tree"></div>
    </div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const skillTreeData = SKILL_TREE_DATA;
        
        let svg, g, zoom, root, tooltip;
        let currentTransform = d3.zoomIdentity;
        
        function init() {
            tooltip = d3.select("#tooltip");
            
            svg = d3.select("#skill-tree")
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%");
            
            g = svg.append("g");
            
            zoom = d3.zoom()
                .scaleExtent([0.1, 3])
                .on("zoom", (event) => {
                    currentTransform = event.transform;
                    g.attr("transform", event.transform);
                });
            
            svg.call(zoom);
            
            root = d3.hierarchy(skillTreeData);
            root.x0 = 0;
            root.y0 = 0;
            root.descendants().forEach((d, i) => {
                d.id = i;
                d._children = d.children;
                if (d.depth > 2) d.children = null;
            });
            
            update(root);
        }
        
        function update(source) {
            const treeLayout = d3.tree().size([800, 1000]);
            treeLayout(root);
            
            const nodes = root.descendants();
            const links = root.links();
            
            const node = g.selectAll("g.node")
                .data(nodes, d => d.id);
            
            const nodeEnter = node.enter()
                .append("g")
                .attr("class", d => "node " + (d.children ? "node--internal" : d.data.type === "certification" ? "node--certification" : "node--leaf"))
                .attr("transform", d => `translate(${source.y0},${source.x0})`)
                .on("click", (event, d) => {
                    if (d.children) {
                        d._children = d.children;
                        d.children = null;
                    } else {
                        d.children = d._children;
                    }
                    update(d);
                })
                .on("mouseover", (event, d) => {
                    tooltip
                        .style("opacity", 1)
                        .html(`<strong>${d.data.name}</strong><br/>${d.depth > 0 ? "Click to expand/collapse" : ""}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px");
                })
                .on("mouseout", () => {
                    tooltip.style("opacity", 0);
                });
            
            nodeEnter.append("circle")
                .attr("r", d => d.depth === 0 ? 15 : d.depth === 1 ? 12 : 8)
                .style("fill", d => {
                    if (d.depth === 0) return "#667eea";
                    if (d.data.type === "certification") return "#FF9800";
                    return d.children ? "#764ba2" : "#4CAF50";
                });
            
            nodeEnter.append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children || d._children ? -13 : 13)
                .style("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name)
                .style("font-size", d => d.depth === 0 ? "16px" : d.depth === 1 ? "14px" : "12px");
            
            const nodeUpdate = nodeEnter.merge(node);
            
            nodeUpdate.transition()
                .duration(300)
                .attr("transform", d => `translate(${d.y},${d.x})`);
            
            nodeUpdate.select("circle")
                .attr("r", d => d.depth === 0 ? 15 : d.depth === 1 ? 12 : 8);
            
            const nodeExit = node.exit()
                .transition()
                .duration(300)
                .attr("transform", d => `translate(${source.y},${source.x})`)
                .remove();
            
            const link = g.selectAll("path.link")
                .data(links, d => d.target.id);
            
            const linkEnter = link.enter()
                .insert("path", "g")
                .attr("class", "link")
                .attr("d", d => {
                    const o = {x: source.x0, y: source.y0};
                    return diagonal(o, o);
                });
            
            linkEnter.merge(link)
                .transition()
                .duration(300)
                .attr("d", d => diagonal(d.source, d.target));
            
            link.exit()
                .transition()
                .duration(300)
                .attr("d", d => {
                    const o = {x: source.x, y: source.y};
                    return diagonal(o, o);
                })
                .remove();
            
            nodes.forEach(d => {
                d.x0 = d.x;
                d.y0 = d.y;
            });
        }
        
        function diagonal(s, d) {
            return `M ${s.y} ${s.x}
                    C ${(s.y + d.y) / 2} ${s.x},
                      ${(s.y + d.y) / 2} ${d.x},
                      ${d.y} ${d.x}`;
        }
        
        function zoomIn() {
            svg.transition().call(zoom.scaleBy, 1.5);
        }
        
        function zoomOut() {
            svg.transition().call(zoom.scaleBy, 0.67);
        }
        
        function resetZoom() {
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }
        
        function expandAll() {
            root.descendants().forEach(d => {
                if (d._children) {
                    d.children = d._children;
                    d._children = null;
                }
            });
            update(root);
        }
        
        function collapseAll() {
            root.descendants().forEach(d => {
                if (d.children && d.depth > 1) {
                    d._children = d.children;
                    d.children = null;
                }
            });
            update(root);
        }
        
        init();
    </script>
</body>
</html>"""
        
        # Inject the skill tree data into the HTML
        skill_tree_json = json.dumps(skill_tree, indent=2)
        html_content = html_template.replace('SKILL_TREE_DATA', skill_tree_json)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main entry point."""
    import sys
    
    pdf_path = "AlbertoMejiaResume.pdf"
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: Resume PDF not found at {pdf_path}")
        return
    
    generator = SkillTreeGenerator()
    skill_tree = generator.generate_skill_tree(pdf_path)
    
    print("\n✅ Skill tree generated successfully!")
    print("📄 Open skill_tree.html in your browser to view the visualization")


if __name__ == "__main__":
    main()

