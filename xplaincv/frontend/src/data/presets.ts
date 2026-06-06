export interface Preset {
  name: string;
  category: string;
  concepts: string[];
  labels: string[];
}

export const PRESETS: Preset[] = [
  // ---------- Food ----------
  {
    name: "Pizza",
    category: "Food",
    concepts: [
      "melted cheese",
      "round crust",
      "tomato sauce",
      "basil leaves",
      "italian food",
    ],
    labels: ["pizza", "hamburger", "sushi", "apple pie", "club sandwich"],
  },
  {
    name: "Hamburger",
    category: "Food",
    concepts: [
      "sesame bun",
      "beef patty",
      "lettuce leaf",
      "tomato slice",
      "melted cheese",
    ],
    labels: ["hamburger", "pizza", "hot dog", "club sandwich", "french fries"],
  },
  {
    name: "Sushi",
    category: "Food",
    concepts: [
      "raw fish",
      "white rice",
      "seaweed wrap",
      "soy sauce",
      "japanese cuisine",
    ],
    labels: ["sushi", "ramen", "pizza", "dumplings", "miso soup"],
  },
  {
    name: "Apple Pie",
    category: "Food",
    concepts: [
      "pastry crust",
      "baked apples",
      "cinnamon spice",
      "lattice top",
      "sweet dessert",
    ],
    labels: ["apple pie", "cheesecake", "donuts", "pizza", "carrot cake"],
  },
  {
    name: "French Fries",
    category: "Food",
    concepts: [
      "golden fried potato",
      "thin sticks",
      "salty crisp",
      "deep fried",
      "fast food side",
    ],
    labels: ["french fries", "hamburger", "onion rings", "hot dog", "pizza"],
  },
  {
    name: "Ice Cream",
    category: "Food",
    concepts: [
      "creamy frozen dessert",
      "scoop in cone",
      "sweet vanilla",
      "soft texture",
      "cold sweet treat",
    ],
    labels: ["ice cream", "cheesecake", "donuts", "frozen yogurt", "tiramisu"],
  },

  // ---------- Animal ----------
  {
    name: "Cat",
    category: "Animal",
    concepts: [
      "soft fur",
      "pointed ears",
      "long whiskers",
      "slit pupils",
      "small predator",
    ],
    labels: ["cat", "dog", "rabbit", "fox", "tiger"],
  },
  {
    name: "Dog",
    category: "Animal",
    concepts: [
      "wagging tail",
      "floppy ears",
      "wet nose",
      "four paws",
      "loyal companion",
    ],
    labels: ["dog", "cat", "wolf", "fox", "rabbit"],
  },
  {
    name: "Bird",
    category: "Animal",
    concepts: [
      "feathered wings",
      "sharp beak",
      "perched on branch",
      "two legs",
      "small creature",
    ],
    labels: ["bird", "butterfly", "bat", "chicken", "fish"],
  },

  // ---------- Vehicle ----------
  {
    name: "Car",
    category: "Vehicle",
    concepts: [
      "four wheels",
      "metal body",
      "windshield glass",
      "headlights",
      "passenger vehicle",
    ],
    labels: ["car", "truck", "motorcycle", "bicycle", "bus"],
  },
  {
    name: "Airplane",
    category: "Vehicle",
    concepts: [
      "metal wings",
      "jet engine",
      "long fuselage",
      "flying in sky",
      "passenger aircraft",
    ],
    labels: ["airplane", "helicopter", "rocket", "bird", "drone"],
  },

  // ---------- Plant ----------
  {
    name: "Flower",
    category: "Plant",
    concepts: [
      "colorful petals",
      "green stem",
      "sweet fragrance",
      "blooming bud",
      "garden plant",
    ],
    labels: ["flower", "tree", "grass", "leaf", "fruit"],
  },
];
