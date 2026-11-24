import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("index.html", () => {
  it("shows the still Loading placeholder until the app's script replaces it", () => {
    const html = readFileSync(resolve(__dirname, "../../index.html"), "utf8");
    const root = html.match(/<div id="root">([\s\S]*?)<\/div>\s*<script/)?.[1] ?? "";
    expect(root).toContain('class="loading-screen"');
    expect(root).toContain(">Loading<");
  });
});
