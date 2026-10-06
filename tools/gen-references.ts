/**
 * Regenerates the skills' reference files from pai-portal's contracts so they
 * never drift by hand:
 *
 * - skills/knowledge/references/kinds.md      kinds, sections, statuses, examples
 * - skills/knowledge/references/ontology.md   rels and their allowed kind pairs
 * - skills/views/references/view-catalog.md   pai-view@1 components and props
 * - skills/resources/references/page-types.md built-in page types and blocks
 *
 * Usage (pai-portal checkout with dependencies installed):
 *   PAI_PORTAL=~/worktrees/pai-console-plugin-ref bun tools/gen-references.ts
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const portal = process.env.PAI_PORTAL;
if (!portal) {
	console.error("PAI_PORTAL must point to a pai-portal checkout.");
	process.exit(1);
}
const contracts = join(portal, "packages/contracts/src");
const pluginRoot = resolve(import.meta.dir, "..");

const { kindsCatalog } = await import(join(contracts, "knowledge/kinds.ts"));
const { KNOWLEDGE_ONTOLOGY } = await import(
	join(contracts, "knowledge/ontology.ts")
);
const { PAGE_CATALOG } = await import(join(contracts, "pages/content.ts"));
const { BUILTIN_PAGE_TYPES } = await import(
	join(contracts, "pages/types/registry.ts")
);

const revision = execFileSync("git", ["-C", portal, "rev-parse", "--short", "HEAD"])
	.toString()
	.trim();
const describe = execFileSync("git", [
	"-C",
	portal,
	"log",
	"-1",
	"--format=%cs %s",
])
	.toString()
	.trim();

function header(title: string, source: string): string {
	return [
		`# ${title}`,
		"",
		`> Generado por \`tools/gen-references.ts\` desde pai-portal \`${revision}\` (${describe}), \`${source}\`. No editar a mano: regenerar.`,
		"",
	].join("\n");
}

function write(relative: string, body: string): void {
	const path = join(pluginRoot, relative);
	mkdirSync(dirname(path), { recursive: true });
	writeFileSync(path, `${body.trimEnd()}\n`);
	console.log(`wrote ${relative}`);
}

// --------------------------------------------------------------- kinds ----

type Section = {
	key: string;
	label: string;
	control: string;
	required: boolean;
	help: string;
	maxChars?: number;
	options?: readonly string[];
	columns?: ReadonlyArray<{ key: string; label: string }>;
	rel?: string;
	targetKinds?: readonly string[];
	min?: number;
	max?: number;
};

function sectionLine(section: Section): string {
	const extras: string[] = [section.control];
	if (section.maxChars) extras.push(`≤${section.maxChars}`);
	if (section.options) extras.push(section.options.join("|"));
	if (section.columns)
		extras.push(`columnas: ${section.columns.map((c) => c.key).join(", ")}`);
	if (section.rel)
		extras.push(
			`→ arista \`${section.rel}\`${section.targetKinds ? ` a ${section.targetKinds.join("/")}` : ""}`,
		);
	const required = section.required ? "**obligatorio**" : "opcional";
	return `- \`${section.key}\` (${required}; ${extras.join("; ")}): ${section.help}`;
}

const catalog = kindsCatalog();
const kindLines: string[] = [
	header("Kinds de Conocimiento", "packages/contracts/src/knowledge"),
	"Cada kind tiene una plantilla estricta: una clave que no aparece aquí se rechaza. `properties` lleva exactamente estas claves. Las secciones `refs` materializan aristas al guardar.",
	"",
	"## Heurística para clasificar",
	"",
	catalog.heuristic,
	"",
	`Formato de cita: ${catalog.citationFormat}`,
	"",
	"## Estados",
	"",
	...catalog.statuses.map(
		(s: { status: string; label: string; meaning: string }) =>
			`- \`${s.status}\` (${s.label}): ${s.meaning}`,
	),
	"",
	"## Índice",
	"",
	"| kind | etiqueta | grupo | decide una persona | se resuelve | identificador |",
	"|---|---|---|---|---|---|",
];
for (const kind of catalog.kinds) {
	const id = kind.identifier
		? `\`${kind.identifier.pattern}\`${kind.identifier.required ? " (obligatorio)" : ""}`
		: "—";
	kindLines.push(
		`| \`${kind.kind}\` | ${kind.label} | ${kind.group} | ${kind.humanDecided ? "sí" : "no"} | ${kind.resolvable ? "sí" : "no"} | ${id} |`,
	);
}
for (const kind of catalog.kinds) {
	kindLines.push(
		"",
		`## \`${kind.kind}\` — ${kind.label} (plantilla v${kind.templateVersion})`,
		"",
		kind.description,
		"",
		`Estados: ${kind.statuses.map((s: string) => `\`${s}\``).join(", ")}.`,
		"",
		...kind.sections
			.filter((s: Section) => s.control !== "derived")
			.map(sectionLine),
	);
	if (kind.example) {
		kindLines.push(
			"",
			"Ejemplo de `properties`:",
			"",
			"```json",
			JSON.stringify(kind.example, null, 1),
			"```",
		);
	}
}
write("skills/knowledge/references/kinds.md", kindLines.join("\n"));

// ------------------------------------------------------------ ontology ----

type Entry = {
	rel: string;
	group: string;
	label: string;
	description: string;
	pairs: ReadonlyArray<{ sources: readonly string[]; targets: readonly string[] }>;
	sameKind: boolean;
	manualOnly?: boolean;
};

const allKinds = catalog.kinds.map((k: { kind: string }) => k.kind);
function kindsList(list: readonly string[]): string {
	if (list.length === allKinds.length) return "*todos*";
	if (list.length > allKinds.length / 2) {
		const missing = allKinds.filter((k: string) => !list.includes(k));
		return `*todos menos* ${missing.map((k: string) => `\`${k}\``).join(", ")}`;
	}
	return list.map((k) => `\`${k}\``).join(", ");
}

const ontologyLines: string[] = [
	header("Ontología de Conocimiento", "packages/contracts/src/knowledge/ontology.ts"),
	"Un `knowledge_link` (o un link en `knowledge_create`) solo se acepta si el par source → target aparece aquí. Si no, el error es `ONTOLOGY`.",
	"",
];
const groups = new Map<string, Entry[]>();
for (const entry of Object.values(KNOWLEDGE_ONTOLOGY) as Entry[]) {
	groups.set(entry.group, [...(groups.get(entry.group) ?? []), entry]);
}
for (const [group, entries] of groups) {
	ontologyLines.push(`## ${group}`, "");
	for (const entry of entries) {
		const flags = [
			entry.sameKind ? "mismo kind en ambos extremos" : null,
			entry.manualOnly ? "solo manual" : null,
		].filter(Boolean);
		ontologyLines.push(
			`### \`${entry.rel}\` (${entry.label})${flags.length ? ` — ${flags.join(", ")}` : ""}`,
			"",
			entry.description,
			"",
			...entry.pairs.map(
				(pair) =>
					`- de ${kindsList(pair.sources)} → a ${kindsList(pair.targets)}`,
			),
			"",
		);
	}
}
write("skills/knowledge/references/ontology.md", ontologyLines.join("\n"));

// ---------------------------------------------------------------- views ----

type JsonSchema = {
	type?: string | string[];
	enum?: readonly unknown[];
	anyOf?: JsonSchema[];
	items?: JsonSchema;
	properties?: Record<string, JsonSchema>;
	required?: readonly string[];
	minimum?: number;
	maximum?: number;
	minLength?: number;
	maxLength?: number;
	minItems?: number;
	maxItems?: number;
};

function schemaType(schema: JsonSchema): string {
	if (schema.anyOf) {
		const parts = schema.anyOf.filter((s) => s.type !== "null").map(schemaType);
		const nullable = schema.anyOf.some((s) => s.type === "null");
		return `${parts.join(" | ")}${nullable ? " (null = por defecto)" : ""}`;
	}
	if (schema.enum) return schema.enum.map((v) => JSON.stringify(v)).join("|");
	const bounds: string[] = [];
	if (schema.minLength !== undefined) bounds.push(`min ${schema.minLength}`);
	if (schema.maxLength !== undefined) bounds.push(`≤${schema.maxLength}`);
	if (schema.minimum !== undefined) bounds.push(`≥${schema.minimum}`);
	if (schema.maximum !== undefined) bounds.push(`≤${schema.maximum}`);
	if (schema.minItems !== undefined) bounds.push(`min ${schema.minItems}`);
	if (schema.maxItems !== undefined) bounds.push(`máx ${schema.maxItems}`);
	const suffix = bounds.length ? ` (${bounds.join(", ")})` : "";
	if (schema.type === "array" && schema.items)
		return `[${schemaType(schema.items)}]${suffix}`;
	if (schema.type === "object" && schema.properties) {
		const fields = Object.entries(schema.properties).map(
			([key, value]) =>
				`${key}${schema.required?.includes(key) ? "" : "?"}: ${schemaType(value)}`,
		);
		return `{ ${fields.join(", ")} }${suffix}`;
	}
	return `${Array.isArray(schema.type) ? schema.type.join("|") : (schema.type ?? "any")}${suffix}`;
}

const views = PAGE_CATALOG.views;
const viewLines: string[] = [
	header(`Catálogo de vistas \`${views.catalog}\``, "packages/views/src/catalog.ts"),
	`Formato: ${views.format}`,
	"",
	"## Reglas",
	"",
	...views.rules.map((rule: string) => `- ${rule}`),
	"",
	"## Límites",
	"",
	...Object.entries(views.limits).map(([k, v]) => `- ${k}: ${v}`),
	"",
	"## Componentes",
	"",
	"Las props que aceptan `null` son opcionales en la práctica: si se omiten toman su valor por defecto. Las demás son obligatorias.",
	"",
];
for (const component of views.components as Array<{
	type: string;
	description: string;
	children: boolean;
	props: JsonSchema;
}>) {
	viewLines.push(
		`### ${component.type}${component.children ? " (admite hijos)" : ""}`,
		"",
		component.description,
		"",
		...Object.entries(component.props.properties ?? {}).map(
			([key, value]) => `- \`${key}\`: ${schemaType(value)}`,
		),
		"",
	);
}
viewLines.push(
	"## Ejemplo del catálogo",
	"",
	"```json",
	JSON.stringify(views.example, null, 1),
	"```",
);
write("skills/views/references/view-catalog.md", viewLines.join("\n"));

// ----------------------------------------------------------- page types ----

type PageType = {
	slug: string;
	version: number;
	label: string;
	description: string;
	sections: Array<{
		id: string;
		title: string;
		required: boolean;
		allowedBlocks: string[];
		minBlocks: number;
		guidance: string;
	}>;
	constraints: {
		minSources: number;
		requiresQuizAfterSection: boolean;
		maxBlocksPerSection: number;
		requiredBlockTypes: string[];
	};
	authoringGuide: string;
};

const blockLines = (PAGE_CATALOG.blocks as Array<{ type: string; description?: string; purpose?: string }>).map(
	(block) =>
		`- \`${block.type}\`: ${block.description ?? block.purpose ?? ""}`.trimEnd(),
);
const typeLines: string[] = [
	header("Tipos de page y bloques", "packages/contracts/src/pages"),
	"## Límites del contenido",
	"",
	...Object.entries(PAGE_CATALOG.limits).map(([k, v]) => `- ${k}: ${v}`),
	"",
	"## Reglas del catálogo",
	"",
	...PAGE_CATALOG.rules.map((rule: string) => `- ${rule}`),
	"",
	"## Bloques",
	"",
	...blockLines,
	"",
	"## Tipos built-in",
	"",
	"Ninguno admite el bloque `view`: una page con vista se crea sin `typeSlug` (o con un tipo de la organización o del proyecto que lo permita). Los tipos de la organización o del proyecto se listan con `page_types`.",
	"",
];
for (const type of BUILTIN_PAGE_TYPES as PageType[]) {
	const c = type.constraints;
	typeLines.push(
		`### \`${type.slug}\` — ${type.label} (v${type.version})`,
		"",
		type.description,
		"",
		`Constraints: minSources ${c.minSources}, maxBlocksPerSection ${c.maxBlocksPerSection}${c.requiresQuizAfterSection ? ", quiz tras cada sección" : ""}${c.requiredBlockTypes.length ? `, bloques obligatorios: ${c.requiredBlockTypes.join(", ")}` : ""}.`,
		"",
		"| sección | obligatoria | bloques permitidos | mín. |",
		"|---|---|---|---|",
		...type.sections.map(
			(s) =>
				`| \`${s.id}\` ${s.title} | ${s.required ? "sí" : "no"} | ${s.allowedBlocks.join(", ")} | ${s.minBlocks} |`,
		),
		"",
	);
}
write("skills/resources/references/page-types.md", typeLines.join("\n"));
