/**
 * Validates every example the skills teach against pai-portal's real
 * contracts, so a skill never shows an input the server would reject.
 *
 * An example is `skills/<skill>/examples/*.json`:
 *   { "tool": "knowledge_create" | "page_create" | "page_update" | "view_render", "input": {...} }
 * or an array of those (a sequence of calls).
 *
 * Usage (pai-portal checkout with dependencies installed):
 *   PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/validate-examples.ts
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const portal = process.env.PAI_PORTAL;
if (!portal) {
	console.error("PAI_PORTAL must point to a pai-portal checkout.");
	process.exit(1);
}
const contracts = join(portal, "packages/contracts/src");
const pluginRoot = resolve(import.meta.dir, "..");

const { createKnowledgeNodeSchema } = await import(
	join(contracts, "knowledge/write.ts")
);
const { getTemplate } = await import(
	join(contracts, "knowledge/templates/index.ts")
);
const { validatePageContent } = await import(
	join(contracts, "pages/types/validate.ts")
);
const { findBuiltinPageType } = await import(
	join(contracts, "pages/types/registry.ts")
);
const { validateViewSpec } = await import(
	join(portal, "packages/views/src/spec.ts")
);

type Call = { tool: string; input: Record<string, unknown> };

const PROJECT_KEYS = ["organizationId", "projectId"];
const PAGE_CREATE_KEYS = new Set([
	...PROJECT_KEYS,
	"path",
	"title",
	"description",
	"type",
	"typeSlug",
	"typeVersion",
	"audience",
	"content",
	"summary",
	"idempotencyKey",
]);
const PAGE_UPDATE_KEYS = new Set([
	...PROJECT_KEYS,
	"path",
	"expectedDocumentId",
	"expectedRevision",
	"content",
	"summary",
	"typeSlug",
	"typeVersion",
	"detachType",
]);

function withoutProject(input: Record<string, unknown>) {
	const rest = { ...input };
	for (const key of PROJECT_KEYS) delete rest[key];
	return rest;
}

function knowledgeCreate(input: Record<string, unknown>): string[] {
	const problems: string[] = [];
	const parsed = createKnowledgeNodeSchema.safeParse(withoutProject(input));
	if (!parsed.success) {
		for (const issue of parsed.error.issues)
			problems.push(`${issue.path.join(".")}: ${issue.message}`);
		return problems;
	}
	if (!parsed.data.sources?.length)
		problems.push("sources: un agente debe dar al menos una fuente (SOURCE_REQUIRED)");
	const template = getTemplate(parsed.data.kind);
	const properties = template.schema.safeParse(parsed.data.properties);
	if (!properties.success)
		for (const issue of properties.error.issues)
			problems.push(`properties.${issue.path.join(".")}: ${issue.message}`);
	return problems;
}

function pageWrite(input: Record<string, unknown>, allowed: Set<string>): string[] {
	const problems = Object.keys(input)
		.filter((key) => !allowed.has(key))
		.map((key) => `${key}: clave no admitida por la tool`);
	const slug = input.typeSlug as string | undefined;
	const type = slug ? findBuiltinPageType(slug) : null;
	if (slug && !type) problems.push(`typeSlug: ${slug} no es un tipo built-in`);
	const result = validatePageContent(input.content, type);
	for (const issue of result.issues)
		problems.push(`content.${issue.path} [${issue.code}]: ${issue.message}`);
	if (typeof input.summary === "string" && input.summary.length > 80)
		problems.push("summary: más de 80 caracteres");
	return problems;
}

function viewRender(input: Record<string, unknown>): string[] {
	const problems = Object.keys(input)
		.filter((key) => key !== "title" && key !== "spec")
		.map((key) => `${key}: clave no admitida por la tool`);
	if (typeof input.title !== "string" || !input.title || input.title.length > 160)
		problems.push("title: obligatorio, de 1 a 160 caracteres");
	const result = validateViewSpec(input.spec);
	for (const issue of result.issues ?? [])
		problems.push(`spec.${issue.path ?? ""}: ${issue.message}`);
	return problems;
}

function check(call: Call): string[] {
	switch (call.tool) {
		case "knowledge_create":
			return knowledgeCreate(call.input);
		case "page_create":
			return pageWrite(call.input, PAGE_CREATE_KEYS);
		case "page_update":
			return pageWrite(call.input, PAGE_UPDATE_KEYS);
		case "view_render":
			return viewRender(call.input);
		default:
			return [`tool ${call.tool}: el validador no la conoce`];
	}
}

function examples(dir: string): string[] {
	const found: string[] = [];
	for (const entry of readdirSync(dir)) {
		const path = join(dir, entry);
		if (statSync(path).isDirectory()) found.push(...examples(path));
		else if (path.includes("/examples/") && path.endsWith(".json")) found.push(path);
	}
	return found;
}

let failures = 0;
const files = examples(join(pluginRoot, "skills")).sort();
for (const file of files) {
	const parsed = JSON.parse(readFileSync(file, "utf8")) as Call | Call[];
	const calls = Array.isArray(parsed) ? parsed : [parsed];
	calls.forEach((call, index) => {
		const problems = check(call);
		const name = `${relative(pluginRoot, file)}${calls.length > 1 ? `#${index}` : ""} (${call.tool})`;
		if (problems.length === 0) {
			console.log(`ok   ${name}`);
			return;
		}
		failures += 1;
		console.log(`FAIL ${name}`);
		for (const problem of problems) console.log(`     ${problem}`);
	});
}
console.log(`\n${files.length} archivos, ${failures} fallos`);
process.exit(failures === 0 ? 0 : 1);
