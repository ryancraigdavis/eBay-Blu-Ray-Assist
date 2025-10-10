<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	let fileInput;
	let dragActive = false;

	function handleFileSelect(event) {
		const files = Array.from(event.target.files);
		processFiles(files);
	}

	function handleDrop(event) {
		event.preventDefault();
		dragActive = false;
		const files = Array.from(event.dataTransfer.files);
		processFiles(files);
	}

	function handleDragOver(event) {
		event.preventDefault();
		dragActive = true;
	}

	function handleDragLeave(event) {
		event.preventDefault();
		dragActive = false;
	}

	function processFiles(files) {
		const imageFiles = files.filter(file => file.type.startsWith('image/'));

		const processedImages = imageFiles.map(file => {
			const url = URL.createObjectURL(file);
			// Extract title from filename (remove extension and clean up)
			let title = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
			title = title.replace(/[-_]/g, ' '); // Replace dashes and underscores with spaces
			title = title.replace(/\b\w/g, l => l.toUpperCase()); // Capitalize first letter of each word

			return {
				file,
				url,
				title,
				originalFilename: file.name
			};
		});

		dispatch('imagesUploaded', { images: processedImages });

		// Reset file input
		if (fileInput) {
			fileInput.value = '';
		}
	}

	function triggerFileSelect() {
		fileInput.click();
	}
</script>

<style>
	.upload-area {
		border: 2px dashed #ccc;
		border-radius: 8px;
		padding: 40px;
		text-align: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.upload-area:hover,
	.upload-area.drag-active {
		border-color: #007bff;
		background-color: #f8f9fa;
	}

	.upload-text {
		color: #666;
		margin: 10px 0;
	}

	.upload-button {
		background: #007bff;
		color: white;
		border: none;
		padding: 12px 24px;
		border-radius: 6px;
		cursor: pointer;
		font-size: 16px;
		margin-top: 10px;
	}

	.upload-button:hover {
		background: #0056b3;
	}

	.file-input {
		display: none;
	}

	.upload-icon {
		font-size: 48px;
		color: #ccc;
		margin-bottom: 10px;
	}
</style>

<div
	class="upload-area"
	class:drag-active={dragActive}
	on:drop={handleDrop}
	on:dragover={handleDragOver}
	on:dragleave={handleDragLeave}
	on:click={triggerFileSelect}
	role="button"
	tabindex="0"
>
	<div class="upload-icon">📁</div>
	<div class="upload-text">
		<strong>Click to select images</strong> or drag and drop here
	</div>
	<div class="upload-text">
		Supports JPG, PNG, WebP formats
	</div>
	<button class="upload-button" type="button">
		Choose Images
	</button>
</div>

<input
	bind:this={fileInput}
	class="file-input"
	type="file"
	multiple
	accept="image/*"
	on:change={handleFileSelect}
/>