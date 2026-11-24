// When the Librarian stops (docs/librarian-plan.md, Silence; docs/LIBRARIAN_SPEC.md §4). This is the
// client's copy of the server's list (api/trove/interview/silence.py), so the answer goes quiet the
// moment it matches, before any call. Silence is about what an answer is about, not a passing word:
// "I miss my mom's lasagna" is a food story. Keep the two lists the same.

const HARMLESS = [
  "oh my god",
  "death metal",
  "bored to death",
  "scared to death",
  "to death",
  "dying to",
  "killing me",
  "killing it",
  "killed it",
  "chronically online",
  "dead serious",
  "dead end",
  "deadline",
  "dead tired",
  "drop[- ]dead",
  "heart of the",
  "broke(n)? the (build|record|story|news)",
  "came out (of|on|in|to be|with|fine|well|better|worse|great|late|early|ahead|okay|ok|right)",
  "transition(ed|ing)? (to|from|into|between)",
];

const SUBJECTS = [
  // grief or death
  "\\b(died|dying|death|deaths|passed away|passing of|funeral|funerals|grief|grieving|grieve|bereave\\w*|miscarr\\w*|stillborn|lost my (mom|dad|mother|father|brother|sister|son|daughter|wife|husband|partner|grand\\w+|aunt|uncle|cousin|friend|best friend|baby)|suicide|killed (himself|herself|themselves))\\b",
  // illness
  "\\b(cancer|chemo\\w*|tumou?r|diagnosed with|terminally ill|depress\\w+|anxiety disorder|panic attacks?|eating disorder|anorexi\\w*|bulimi\\w*|bipolar|schizo\\w*|ptsd|adhd|autis\\w+|seizures?|epilep\\w+|my illness|chronic (illness|pain)|hospitali[sz]ed|was in the hospital|my surgery|rehab|addiction|in recovery|relapse\\w*|overdos\\w+|in therapy|my therapist|mental health|burn(ed|t)? out|burnout|disabilit\\w+|disabled)\\b",
  // family trouble
  "\\b(divorc\\w+|custody|estranged|kicked (me )?out|disowned|foster (care|home|family)|my parents (split|separated|fought)|separated from my|domestic violence)\\b",
  // abuse or self-harm
  "\\b(abused|abusive|child abuse|sexual abuse|abuse at home|assault\\w*|rape\\w*|molest\\w*|self[- ]harm\\w*|cutting myself|hurt myself|harass\\w+|stalked|stalker|groomed)\\b",
  // heartbreak
  "\\b(broke up|breakup|break-up|broken heart|heartbr\\w+|my ex\\b|dumped me|cheated on)\\b",
  // sexuality or gender as the subject
  "\\b(coming out|came out|my sexuality|my gender|gender identity|transgender|trans\\b|non-?binary|i'?m gay|being gay|lesbian|bisexual|queer|my pronouns)\\b",
  // faith as a struggle
  "\\b(lost my faith|crisis of faith|left the church|leaving my religion|questioning god)\\b",
  // legal or immigration status
  "\\b(deport\\w*|undocumented|visa status|green card|asylum|refugee\\w*|immigration status|arrested|incarcerat\\w+|prison|jail|probation|parole|convicted|lawsuit)\\b",
].map((pattern) => new RegExp(pattern, "i"));

const HARMLESS_PATTERN = new RegExp(HARMLESS.map((p) => `(?:${p})`).join("|"), "gi");

export function isSilent(text: string): boolean {
  const cleaned = text.replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(HARMLESS_PATTERN, " ");
  return SUBJECTS.some((pattern) => pattern.test(cleaned));
}
