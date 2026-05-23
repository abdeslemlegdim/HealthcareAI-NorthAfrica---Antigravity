const IS_TOUCH = navigator.maxTouchPoints > 0;
const LAYERS = ["EARTH", "BODY", "MIND", "SPIRIT", "VOID"];
const LERP = 0.1;
const clamp = (val, min, max) => Math.min(Math.max(val, min), max);

const createScroller = (options = {}) => {
	const scrollElement = document.querySelector(".scroll-track");
	if (!scrollElement) return null;
	const onProgress = options.onProgress || null;
	let currentY = 0;
	let targetY = 0;
	let raf = null;
	let lastTime = null;
	let touchRaf = null;
	let pendingY = null;

	const travel = () =>
		Math.max(0, scrollElement.scrollHeight - window.innerHeight);

	const setY = (y) => {
		scrollElement.style.transform = `translate3d(0, ${y}px, 0)`;
	};

	const updateHeight = () => {
		const h = `${scrollElement.scrollHeight}px`;
		if (document.body.style.height !== h) document.body.style.height = h;
	};

	const tick = (time) => {
		if (!lastTime) lastTime = time;
		const delta = (time - lastTime) / 16.666;
		lastTime = time;
		const lerpFactor = 1 - Math.pow(1 - LERP, delta);
		const diff = targetY - currentY;
		if (Math.abs(diff) > 0.01) {
			currentY += diff * lerpFactor;
			setY(currentY);
		} else if (currentY !== targetY) {
			currentY = targetY;
			setY(currentY);
		}
		raf = requestAnimationFrame(tick);
	};

	const onScroll = () => {
		const t = travel();
		const y = -t + window.scrollY;
		if (IS_TOUCH) {
			pendingY = y;
			if (!touchRaf) {
				touchRaf = requestAnimationFrame(() => {
					currentY = targetY = pendingY;
					setY(pendingY);
					touchRaf = null;
				});
			}
		} else {
			targetY = y;
		}
		const progress = t > 0 ? window.scrollY / t : 0;
		onProgress?.(clamp(progress, 0, 1));
	};

	const onResize = () => {
		const t = travel();
		if (IS_TOUCH) {
			currentY = targetY = -t + window.scrollY;
			setY(currentY);
		} else {
			targetY = -t + window.scrollY;
		}
		const progress = t > 0 ? window.scrollY / t : 0;
		onProgress?.(clamp(progress, 0, 1));
	};

	const scrollToPanel = (index) => {
		const clamped = clamp(index, 0, LAYERS.length - 1);
		const progress = clamped / (LAYERS.length - 1);
		window.scrollTo({ top: travel() * progress });
	};

	const destroy = () => {
		if (raf) cancelAnimationFrame(raf);
		if (touchRaf) cancelAnimationFrame(touchRaf);
		resizeObserver.disconnect();
		window.removeEventListener("scroll", onScroll);
		window.removeEventListener("resize", onResize);
	};

	updateHeight();

	const resizeObserver = new ResizeObserver(() => {
		updateHeight();
		const t = travel();
		if (IS_TOUCH) {
			currentY = targetY = -t + window.scrollY;
			setY(currentY);
		} else {
			targetY = -t + window.scrollY;
		}
		const progress = t > 0 ? window.scrollY / t : 0;
		onProgress?.(clamp(progress, 0, 1));
	});
	resizeObserver.observe(scrollElement);

	const t = travel();
	const initialY = -t + clamp(window.scrollY, 0, t);
	currentY = initialY;
	targetY = initialY;
	setY(currentY);
	const initialProgress = t > 0 ? window.scrollY / t : 0;
	onProgress?.(clamp(initialProgress, 0, 1));

	window.addEventListener("scroll", onScroll, { passive: true });
	window.addEventListener("resize", onResize, { passive: true });

	if (!IS_TOUCH) {
		raf = requestAnimationFrame(tick);
	}

	return { scrollToPanel, destroy };
};

const ui = (() => {
	const fill = document.getElementById("progress_fill");
	const label = document.getElementById("hud_label");
	const dots = [...document.querySelectorAll(".nav-dot")];
	const scene = document.querySelector(".scene");
	let lastIndex = -1;
	return {
		update(progress) {
			const p = clamp(progress, 0, 1);
			if (fill) fill.style.width = `${p * 100}%`;
			if (scene) scene.style.backgroundPositionY = `${(1 - p) * 100}%`;
			const index = Math.min(Math.floor(p * LAYERS.length), LAYERS.length - 1);
			if (index !== lastIndex) {
				lastIndex = index;
				if (label) label.textContent = LAYERS[index];
				dots.forEach((dot, i) => dot.classList.toggle("is-active", i === index));
			}
		}
	};
})();

const initialize = () => {
	const run = () => {
		document.fonts.ready.then(() => {
			const scroller = createScroller({
				onProgress: (progress) => ui.update(progress)
			});
			document.querySelectorAll(".nav-dot").forEach((dot) => {
				dot.addEventListener("click", () => {
					scroller?.scrollToPanel(Number(dot.dataset.index));
				});
			});
		});
	};
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", run, { once: true });
	} else {
		run();
	}
};

initialize();
