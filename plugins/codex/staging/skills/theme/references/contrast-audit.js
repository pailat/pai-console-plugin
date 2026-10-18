// Auditoría de contraste del tema en el Portal de Pai. Se pega en la pestaña del
// Portal (javascript_tool de Chrome o la consola) con la organización abierta.
//
// Claro: recarga la página, espera a que termine de pintar y pega todo el
// archivo. Define paiForceDark() y paiContrastAudit() y mide.
// Oscuro, sin cambiar la preferencia de la persona:
//   1. Llama paiForceDark(). Pasa la página a oscuro y la mantiene así, porque
//      el tema revierte la clase.
//   2. Espera a que terminen las transiciones (1–2 s) y llama paiContrastAudit().
//      Si mides en el mismo instante del cambio, las transiciones de CSS dan
//      falsos 1.02.
//
// Devuelve una línea con el modo, cuántos textos midió, el contraste mínimo y las
// superficies border/background, muted/background, secondary/background y
// sidebar-accent/sidebar. Debajo, los textos que no llegan a AA (4.5 normal,
// 3 desde 24px), con su contraste y los primeros 26 caracteres.
//
// - Las opacidades se componen pintando en un canvas en orden, nunca mezclando
//   alfa a mano. Mezclarlo a mano aplicó el alfa dos veces y dio falsos 3.18 y 4.14.
// - Excluye los textos con «@», porque la extensión de Chrome bloquea las salidas
//   con datos que parecen correos o query strings.

// --- forzar oscuro ---------------------------------------------------------
function paiForceDark() {
	const root = document.documentElement;
	const hold = () => {
		if (!root.classList.contains("dark")) {
			root.classList.remove("light");
			root.classList.add("dark");
		}
	};
	hold();
	window.__paiDarkObserver?.disconnect();
	window.__paiDarkObserver = new MutationObserver(hold);
	window.__paiDarkObserver.observe(root, { attributes: true, attributeFilter: ["class"] });
	return "oscuro forzado; espera 1–2 s y mide";
}
// Para volver a claro: window.__paiDarkObserver?.disconnect() y recarga.

// --- medir -----------------------------------------------------------------
function paiContrastAudit() {
	const cv = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
	const paint = (cols) => {
		cv.clearRect(0, 0, 1, 1);
		cv.fillStyle = "#fff";
		cv.fillRect(0, 0, 1, 1);
		for (const c of cols) {
			cv.fillStyle = c;
			cv.fillRect(0, 0, 1, 1);
		}
		const d = cv.getImageData(0, 0, 1, 1).data;
		return [d[0], d[1], d[2]];
	};
	const lum = ([r, g, b]) => {
		const f = (v) => {
			v /= 255;
			return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
		};
		return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
	};
	const ratio = (a, b) => {
		const l1 = lum(a);
		const l2 = lum(b);
		return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
	};
	// Los fondos de abajo hacia arriba hasta el primero opaco.
	const stack = (el) => {
		const layers = [];
		for (let e = el; e; e = e.parentElement) {
			const c = getComputedStyle(e).backgroundColor;
			if (c === "rgba(0, 0, 0, 0)") continue;
			layers.unshift(c);
			if (!/\/|rgba/.test(c)) break;
		}
		return layers;
	};

	const bad = [];
	const seen = new Set();
	let n = 0;
	let min = 99;
	for (const el of document.querySelectorAll("body *")) {
		const t = [...el.childNodes]
			.filter((x) => x.nodeType === 3)
			.map((x) => x.textContent.trim())
			.join(" ")
			.trim();
		if (!t || t.includes("@")) continue;
		if (!el.getBoundingClientRect().width) continue;
		const s = getComputedStyle(el);
		const layers = stack(el);
		const cr = ratio(paint([...layers, s.color]), paint(layers));
		n++;
		min = Math.min(min, cr);
		const need = parseFloat(s.fontSize) >= 24 ? 3 : 4.5;
		const k = t.slice(0, 26);
		if (cr < need && !seen.has(k)) {
			seen.add(k);
			bad.push(`${cr.toFixed(2)} ${k}`);
		}
	}

	const token = (x) => paint([getComputedStyle(document.documentElement).getPropertyValue(`--${x}`).trim()]);
	const surfaces = [
		["border", "background"],
		["muted", "background"],
		["secondary", "background"],
		["sidebar-accent", "sidebar"],
	]
		.map(([a, b]) => `${a}/${b} ${ratio(token(a), token(b)).toFixed(2)}`)
		.join("  ");
	const mode = document.documentElement.classList.contains("dark") ? "DARK" : "LIGHT";
	return `${mode} | ${n} textos, mín ${min.toFixed(2)} | ${surfaces}\n${bad.join("\n") || "sin fallos AA"}`;
}

paiContrastAudit();
