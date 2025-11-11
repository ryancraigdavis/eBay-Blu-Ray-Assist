<script>
	import ImageUpload from '$lib/ImageUpload.svelte';
	import MovieForm from '$lib/MovieForm.svelte';

	const API_BASE = 'http://localhost:8000';

	let uploadedImages = [];
	let currentIndex = $state(0);
	let submittedItems = $state([]);
	let isDownloading = $state(false);
	let downloadError = $state('');

	function handleImagesUploaded(event) {
		uploadedImages = event.detail.images;
		currentIndex = 0;
		submittedItems = [];
	}

	function handleItemSubmit(item) {
		submittedItems.push(item);

		// Auto-advance to next image if available
		if (currentIndex < uploadedImages.length - 1) {
			currentIndex++;
		}
	}

	function goToPrevious() {
		if (currentIndex > 0) {
			currentIndex--;
		}
	}

	function goToNext() {
		if (currentIndex < uploadedImages.length - 1) {
			currentIndex++;
		}
	}

	function goToImage(index) {
		currentIndex = index;
	}

	function isItemSubmitted(index) {
		return submittedItems.length > index;
	}

	async function downloadCSV() {
		if (submittedItems.length === 0) {
			downloadError = 'No items to export';
			return;
		}

		isDownloading = true;
		downloadError = '';

		try {
			const response = await fetch(`${API_BASE}/template/generate-csv`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(submittedItems)
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			// Get the blob and create download
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `ebay_bluray_listings_${submittedItems.length}_items.csv`;
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);

		} catch (error) {
			downloadError = `Failed to generate CSV: ${error.message}`;
		} finally {
			isDownloading = false;
		}
	}
</script>

<style>
	.upload-section {
		background: white;
		padding: 20px;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		margin-bottom: 20px;
	}

	.progress-section {
		background: white;
		padding: 20px;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		margin-bottom: 20px;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
	}

	.progress-title {
		font-size: 20px;
		font-weight: 600;
		color: #333;
	}

	.progress-counter {
		font-size: 16px;
		color: #666;
	}

	.image-thumbnails {
		display: flex;
		gap: 10px;
		overflow-x: auto;
		padding: 10px 0;
	}

	.thumbnail {
		width: 80px;
		height: 80px;
		border-radius: 4px;
		object-fit: cover;
		cursor: pointer;
		border: 3px solid transparent;
		transition: border-color 0.2s;
	}

	.thumbnail.active {
		border-color: #007bff;
	}

	.thumbnail.submitted {
		border-color: #28a745;
		opacity: 0.7;
	}

	.thumbnail:hover {
		opacity: 0.8;
	}

	.navigation-buttons {
		display: flex;
		gap: 10px;
		margin-top: 15px;
	}

	.nav-btn {
		padding: 10px 20px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		background: #6c757d;
		color: white;
		transition: background-color 0.2s;
	}

	.nav-btn:hover:not(:disabled) {
		background: #5a6268;
	}

	.nav-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.movie-item {
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		padding: 20px;
	}

	.csv-section {
		background: white;
		padding: 30px;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		margin-top: 20px;
		text-align: center;
	}

	.csv-section h2 {
		color: #333;
		margin-bottom: 10px;
	}

	.csv-section p {
		color: #666;
		margin-bottom: 20px;
	}

	.download-btn {
		padding: 15px 40px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 18px;
		font-weight: 600;
		background: #28a745;
		color: white;
		transition: background-color 0.2s;
	}

	.download-btn:hover:not(:disabled) {
		background: #218838;
	}

	.download-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #dc3545;
		margin-top: 10px;
		font-size: 14px;
	}

	.status-badge {
		display: inline-block;
		padding: 5px 10px;
		border-radius: 4px;
		font-size: 12px;
		font-weight: 600;
		margin-left: 10px;
	}

	.status-submitted {
		background: #d4edda;
		color: #155724;
	}

	.status-pending {
		background: #fff3cd;
		color: #856404;
	}
</style>

<div class="upload-section">
	<h2>Upload Blu-ray Images</h2>
	<p>Select one or more images of your Blu-ray movies. You'll fill out each listing one at a time.</p>
	<ImageUpload on:imagesUploaded={handleImagesUploaded} />
</div>

{#if uploadedImages.length > 0}
	<!-- Progress Section -->
	<div class="progress-section">
		<div class="progress-header">
			<div>
				<span class="progress-title">Listing Progress</span>
				{#if isItemSubmitted(currentIndex)}
					<span class="status-badge status-submitted">✓ Submitted</span>
				{:else}
					<span class="status-badge status-pending">Pending</span>
				{/if}
			</div>
			<div class="progress-counter">
				Image {currentIndex + 1} of {uploadedImages.length}
			</div>
		</div>

		<!-- Thumbnail Navigation -->
		<div class="image-thumbnails">
			{#each uploadedImages as image, index}
				<img
					src={image.url}
					alt={image.title}
					class="thumbnail"
					class:active={index === currentIndex}
					class:submitted={isItemSubmitted(index)}
					on:click={() => goToImage(index)}
					title="{image.title} {isItemSubmitted(index) ? '(Submitted)' : ''}"
				/>
			{/each}
		</div>

		<!-- Navigation Buttons -->
		<div class="navigation-buttons">
			<button
				class="nav-btn"
				on:click={goToPrevious}
				disabled={currentIndex === 0}
			>
				← Previous
			</button>
			<button
				class="nav-btn"
				on:click={goToNext}
				disabled={currentIndex === uploadedImages.length - 1}
			>
				Next →
			</button>
		</div>
	</div>

	<!-- Current Movie Form -->
	<div class="movie-item">
		<MovieForm
			image={uploadedImages[currentIndex]}
			movieIndex={currentIndex}
			onSubmit={handleItemSubmit}
		/>
	</div>

	<!-- CSV Download Section -->
	{#if submittedItems.length > 0}
		<div class="csv-section">
			<h2>Export to eBay CSV</h2>
			<p>
				You've submitted {submittedItems.length} of {uploadedImages.length} items.
				{#if submittedItems.length === uploadedImages.length}
					All items are ready to export!
				{:else}
					You can export now or continue adding more items.
				{/if}
			</p>
			<button
				class="download-btn"
				on:click={downloadCSV}
				disabled={isDownloading}
			>
				{isDownloading ? 'Generating CSV...' : `Download CSV (${submittedItems.length} items)`}
			</button>
			{#if downloadError}
				<div class="error">{downloadError}</div>
			{/if}
		</div>
	{/if}
{/if}