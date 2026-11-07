// SAMPLE DATA, not real members. A static preview of the shelf until the database seed (plan item B1)
// and the books API replace this file. Every name is invented. Books show the author's full name.

export interface SampleBook {
  id: string;
  title: string;
  authorName: string;
  chapters: string[];
}

export interface SampleShelf {
  /** A placeholder name: shelf categories are not decided yet. */
  name: string;
  bookIds: string[];
}

export const sampleBooks: SampleBook[] = [
  {
    id: "sample-hana",
    title: "Why I Turned Down Grad School Twice",
    authorName: "Hana Sato",
    chapters: ["The first offer", "What the funding letter didn't say", "Asking again, three years later"],
  },
  {
    id: "sample-dana",
    title: "How to Leave a Job Without Burning the Bridge",
    authorName: "Dana Whitcomb",
    chapters: ["Telling your manager first", "The last two weeks", "Staying in touch"],
  },
  {
    id: "sample-marcus",
    title: "Switching Off Pre-Med Before Telling Your Parents",
    authorName: "Marcus Bell",
    chapters: ["The semester I knew", "Finding a major that fit", "The phone call home"],
  },
  {
    id: "sample-kiera",
    title: "From Orchestra Pit to Product Manager",
    authorName: "Kiera Lindgren",
    chapters: [
      "What rehearsal teaches about deadlines",
      "My first interview outside music",
      "Reading a room",
    ],
  },
  {
    id: "sample-luis",
    title: "Teaching Yourself to Code at Thirty-Four",
    authorName: "Luis Ortega",
    chapters: [
      "Nights and weekends",
      "The first project someone used",
      "Getting hired without a degree in it",
    ],
  },
  {
    id: "sample-priya",
    title: "The First Year Running a Shop Alone",
    authorName: "Priya Raman",
    chapters: ["Signing the lease", "Slow months", "Hiring the first person"],
  },
  {
    id: "sample-tomas",
    title: "What Nobody Said About Moving Abroad",
    authorName: "Tomas Novak",
    chapters: ["Visas and paperwork", "The lonely third month", "Building a new circle"],
  },
  {
    id: "sample-jonah",
    title: "Coming Home After Ten Years Away",
    authorName: "Jonah Feld",
    chapters: ["Why Cleveland", "Old friends, new people"],
  },
  {
    id: "sample-mei",
    title: "Leaving Engineering for the Classroom",
    authorName: "Mei Chen",
    chapters: ["The pay cut", "Getting certified", "What I still use from engineering", "Year one"],
  },
  {
    id: "sample-omar",
    title: "Three Cities, One Career",
    authorName: "Omar Haddad",
    chapters: ["Chicago", "Austin", "Choosing where to stay"],
  },
  {
    id: "sample-amara",
    title: "Raising Money Without a Network",
    authorName: "Amara Eze",
    chapters: ["The first hundred cold emails", "Pitch competitions worth entering", "Closing a seed round"],
  },
  {
    id: "sample-ben",
    title: "Learning to Say No at Work",
    authorName: "Ben Carver",
    chapters: ["The overloaded first job", "Saying no to a director", "What changed afterwards"],
  },
  {
    id: "sample-ruth",
    title: "A Late Start in Nursing",
    authorName: "Ruth Adler",
    chapters: [
      "Prerequisites at twenty-nine",
      "Clinicals with classmates half my age",
      "The first night shift",
    ],
  },
  {
    id: "sample-noel",
    title: "Selling the Family Farm, Keeping the Land",
    authorName: "Noel Fontaine",
    chapters: ["Three generations of soybeans", "Leasing instead of selling", "Telling my grandfather"],
  },
  {
    id: "sample-ines",
    title: "Writing for Money, Then Not",
    authorName: "Ines Duarte",
    chapters: ["Freelance rates", "Burning out on deadlines", "Writing only for myself"],
  },
  {
    id: "sample-rosa",
    title: "Asking for the Raise I Deserved",
    authorName: "Rosa Bianchi",
    chapters: ["Knowing the number", "The meeting", "When the answer is no"],
  },
  {
    id: "sample-pete",
    title: "A Second Degree at Forty",
    authorName: "Pete Kowalczyk",
    chapters: ["Night classes", "Being the oldest in the room", "Using it at work"],
  },
  {
    id: "sample-lena",
    title: "Building a Practice from a Spare Room",
    authorName: "Lena Morales",
    chapters: ["The first three clients", "Insurance paperwork", "Moving into a real office"],
  },
  {
    id: "sample-alexandra",
    title: "Starting a Podcast With No Audience",
    authorName: "Alexandra Okonkwo-Brennan",
    chapters: ["Episode one", "Finding guests", "The listener who wrote back"],
  },
  {
    id: "sample-aditya",
    title: "Two Co-ops Before Graduating",
    authorName: "Aditya Iyer",
    chapters: ["Applying as a sophomore", "Six months at a plant in Akron", "Turning a co-op into an offer"],
  },
  {
    id: "sample-grace",
    title: "Getting Into a Research Lab as a First-Year",
    authorName: "Grace Lindqvist",
    chapters: ["Emailing professors", "Washing glassware for a semester", "My first poster"],
  },
  {
    id: "sample-theo",
    title: "Prototyping a Startup in the Makerspace",
    authorName: "Theo Marchetti",
    chapters: ["Learning the laser cutter", "Ten bad prototypes", "Our first paying customer"],
  },
  {
    id: "sample-jasmine",
    title: "Surviving Organic Chemistry",
    authorName: "Jasmine Torres",
    chapters: ["Why memorizing fails", "Study groups that work", "Office hours, honestly"],
  },
  {
    id: "sample-nadia",
    title: "From Biomedical Engineering to Patent Law",
    authorName: "Nadia Petrova",
    chapters: ["Realizing I liked writing more than the lab", "The patent bar", "Law school at night"],
  },
  {
    id: "sample-eli",
    title: "Running a Student Group Nobody Had Heard Of",
    authorName: "Eli Abrams",
    chapters: ["Four members", "The activities fair", "Handing it on"],
  },
  {
    id: "sample-sofia",
    title: "Matching Into Residency Close to Home",
    authorName: "Sofia Reyes",
    chapters: ["Choosing a specialty", "Away rotations", "Ranking day"],
  },
  {
    id: "sample-malik",
    title: "Two Years in the Peace Corps After Graduation",
    authorName: "Malik Johnson",
    chapters: ["Deciding to go", "Teaching science in Ghana", "Coming back to job interviews"],
  },
  {
    id: "sample-yuki",
    title: "Finding a Mentor Who Wasn't Assigned to Me",
    authorName: "Yuki Tanaka",
    chapters: ["Asking for coffee", "What to bring to the first meeting", "Keeping it going"],
  },
  {
    id: "sample-caleb",
    title: "Turning a Senior Project Into a First Job",
    authorName: "Caleb Moore",
    chapters: ["Picking a project a company needs", "Demo day", "The offer"],
  },
];

export const sampleFeatured = {
  bookId: "sample-hana",
  /** Placeholder for the Librarian's reason; the real one is written for the reader. */
  reason: "You’re deciding about a PhD. Hana weighed the same choice, twice.",
};

export const sampleShelves: SampleShelf[] = [
  {
    name: "Changing course",
    bookIds: [
      "sample-dana",
      "sample-marcus",
      "sample-kiera",
      "sample-luis",
      "sample-priya",
      "sample-tomas",
      "sample-jonah",
      "sample-mei",
      "sample-omar",
    ],
  },
  {
    name: "Starting over",
    bookIds: [
      "sample-amara",
      "sample-ben",
      "sample-ruth",
      "sample-noel",
      "sample-ines",
      "sample-rosa",
      "sample-pete",
      "sample-lena",
      "sample-alexandra",
    ],
  },
  {
    name: "Recently added",
    bookIds: [
      "sample-aditya",
      "sample-grace",
      "sample-theo",
      "sample-jasmine",
      "sample-nadia",
      "sample-eli",
      "sample-sofia",
      "sample-malik",
      "sample-yuki",
      "sample-caleb",
    ],
  },
];
