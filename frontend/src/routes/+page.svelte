<script>
	import ImageUpload from '$lib/ImageUpload.svelte';
	import MovieForm from '$lib/MovieForm.svelte';

	let uploadedImages = [];

	function handleImagesUploaded(event) {
		uploadedImages = event.detail.images;
	}

	function removeImage(index) {
		uploadedImages = uploadedImages.filter((_, i) => i !== index);
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

	.movies-grid {
		display: grid;
		gap: 20px;
	}

	.movie-item {
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		overflow: hidden;
	}

	.remove-btn {
		background: #dc3545;
		color: white;
		border: none;
		padding: 5px 10px;
		border-radius: 4px;
		cursor: pointer;
		font-size: 12px;
		margin-bottom: 10px;
	}

	.remove-btn:hover {
		background: #c82333;
	}
</style>

<div class="upload-section">
	<h2>Upload Blu-ray Images</h2>
	<p>Select one or more images of your Blu-ray movies. Each image will create a separate listing form.</p>
	<ImageUpload on:imagesUploaded={handleImagesUploaded} />
</div>

{#if uploadedImages.length > 0}
	<div class="movies-grid">
		{#each uploadedImages as image, index}
			<div class="movie-item">
				<div style="padding: 15px;">
					<button class="remove-btn" on:click={() => removeImage(index)}>
						Remove
					</button>
					<MovieForm {image} movieIndex={index} />
				</div>
			</div>
		{/each}
	</div>
{/if}