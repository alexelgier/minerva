import re


def extract_sections(text):
    """Extract PANAS, BPNS and Flourishing sections from text."""
    sections = {}

    # Extract PANAS Positive
    panas_pos_match = re.search(
        r"## PANAS.*?Positive Affect.*?Interested::\s*(\d+).*?Excited::\s*(\d+).*?Strong::\s*(\d+).*?Enthusiastic::\s*(\d+).*?Proud::\s*(\d+).*?Alert::\s*(\d+).*?Inspired::\s*(\d+).*?Determined::\s*(\d+).*?Attentive::\s*(\d+).*?Active::\s*(\d+)",
        text, re.DOTALL)
    if panas_pos_match:
        sections['panas_pos'] = [int(val) for val in panas_pos_match.groups()]

    # Extract PANAS Negative
    panas_neg_match = re.search(
        r"Negative Affect.*?Distressed::\s*(\d+).*?Upset::\s*(\d+).*?Guilty::\s*(\d+).*?Scared::\s*(\d+).*?Hostile::\s*(\d+).*?Irritable::\s*(\d+).*?Ashamed::\s*(\d+).*?Nervous::\s*(\d+).*?Jittery::\s*(\d+).*?Afraid::\s*(\d+)",
        text, re.DOTALL)
    if panas_neg_match:
        sections['panas_neg'] = [int(val) for val in panas_neg_match.groups()]

    # Extract BPNS
    bpns_match = re.search(
        r"## BPNS.*?Autonomy.*?I feel like I can make choices about the things I do::\s*(\d+).*?I feel free to decide how I do my daily tasks::\s*(\d+).*?Competence.*?I feel capable at the things I do::\s*(\d+).*?I can successfully complete challenging tasks::\s*(\d+).*?Relatedness.*?I feel close and connected with the people around me::\s*(\d+).*?I get along well with the people I interact with daily::\s*(\d+).*?I feel supported by others in my life::\s*(\d+)",
        text, re.DOTALL)
    if bpns_match:
        sections['bpns'] = [int(val) for val in bpns_match.groups()]

    # Extract Flourishing
    flour_match = re.search(
        r"## Flourishing Scale.*?I lead a purposeful and meaningful life::\s*(\d+).*?My social relationships are supportive and rewarding::\s*(\d+).*?I am engaged and interested in my daily activities::\s*(\d+).*?I actively contribute to the happiness and well-being of others::\s*(\d+).*?I am competent and capable in the activities that are important to me::\s*(\d+).*?I am a good person and live a good life::\s*(\d+).*?I am optimistic about my future::\s*(\d+).*?People respect me::\s*(\d+)",
        text, re.DOTALL)
    if flour_match:
        sections['flourishing'] = [int(val) for val in flour_match.groups()]

    return sections


def calculate_scores(sections):
    """Calculate scores based on extracted sections."""
    scores = {}

    if 'panas_pos' in sections:
        scores['panas_pos_percent'] = (sum(sections['panas_pos']) - 10) / 40 * 100

    if 'panas_neg' in sections:
        scores['panas_neg_percent'] = (sum(sections['panas_neg']) - 10) / 40 * 100

    if 'bpns' in sections:
        autonomy = sum(sections['bpns'][0:2])
        competence = sum(sections['bpns'][2:4])
        relatedness = sum(sections['bpns'][4:7])
        bpns_total = autonomy + competence + relatedness

        scores['bpns_autonomy'] = (autonomy - 2) / 12 * 100
        scores['bpns_competence'] = (competence - 2) / 12 * 100
        scores['bpns_relatedness'] = (relatedness - 3) / 18 * 100
        scores['bpns_total'] = (bpns_total - 7) / 42 * 100

    if 'flourishing' in sections:
        flourishing_total = sum(sections['flourishing'])
        scores['flourishing'] = (flourishing_total - 8) / 48 * 100

    return scores
