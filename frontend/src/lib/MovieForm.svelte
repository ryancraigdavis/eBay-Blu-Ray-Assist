<script>
	let { image, movieIndex, onSubmit } = $props();

	const API_BASE = 'http://localhost:8000';

	// Form data based on eBay template requirements
	let formData = $state({
		// Basic info
		title: image.title,
		condition: 'Used',
		description: '',
		price: '12.99',
		quantity: '1',
		location: 'United States',

		// Movie metadata (from TMDB)
		movieTitle: '',
		studio: '',
		genre: '',
		subGenre: '',
		director: '',
		actors: '',
		releaseYear: '',
		rating: 'PG-13',
		runtime: '',

		// Technical specs
		regionCode: '1',
		language: 'English',
		caseType: 'Standard Blu-ray Case',
		features: '',

		// Images and AWS
		s3Url: '',

		// Pricing data
		averagePrice: '',
		shippingCost: '4.99',
		totalCost: '',

		// User notes
		userNotes: ''
	});

	let loading = {
		metadata: false,
		pricing: false,
		upload: false
	};

	let errors = {
		metadata: '',
		pricing: '',
		upload: '',
		submit: ''
	};

	let isSubmitted = $state(false);

	async function fetchMetadata() {
		loading.metadata = true;
		errors.metadata = '';

		try {
			const response = await fetch(`${API_BASE}/process/metadata?title=${encodeURIComponent(formData.title)}`);

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const metadata = await response.json();

			// Update form with metadata
			formData.movieTitle = metadata.title || formData.title;
			formData.studio = metadata.studio || '';
			formData.genre = metadata.genres?.[0] || '';
			formData.subGenre = metadata.genres?.[1] || '';
			formData.director = metadata.director || '';
			formData.actors = metadata.actors?.join(', ') || '';
			formData.releaseYear = metadata.release_date ? metadata.release_date.split('-')[0] : '';
			formData.rating = metadata.rating || 'PG-13';
			formData.runtime = metadata.runtime ? metadata.runtime.toString() : '';

			// Update description with metadata
			formData.description = generateDescription(metadata);

		} catch (error) {
			errors.metadata = `Failed to fetch metadata: ${error.message}`;
		} finally {
			loading.metadata = false;
		}
	}

	async function fetchPricing() {
		loading.pricing = true;
		errors.pricing = '';

		try {
			const response = await fetch(`${API_BASE}/process/pricing`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					title: formData.title,
					condition: formData.condition
				})
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const pricingData = await response.json();

			// Update form with pricing data
			formData.averagePrice = pricingData.average_price?.toFixed(2) || '';
			formData.shippingCost = pricingData.shipping_cost?.toFixed(2) || '4.99';
			formData.totalCost = pricingData.total_cost?.toFixed(2) || '';

			// Set suggested price (add 15% margin)
			if (pricingData.average_price) {
				formData.price = (pricingData.average_price * 1.15).toFixed(2);
			}

		} catch (error) {
			errors.pricing = `Failed to fetch pricing: ${error.message}`;
		} finally {
			loading.pricing = false;
		}
	}

	async function uploadToAWS() {
		loading.upload = true;
		errors.upload = '';

		try {
			const formDataUpload = new FormData();
			formDataUpload.append('files', image.file);

			const response = await fetch(`${API_BASE}/upload/images`, {
				method: 'POST',
				body: formDataUpload
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const uploadResults = await response.json();

			if (uploadResults && uploadResults.length > 0) {
				formData.s3Url = uploadResults[0].s3_url;
			}

		} catch (error) {
			errors.upload = `Failed to upload to AWS: ${error.message}`;
		} finally {
			loading.upload = false;
		}
	}

	function generateDescription(metadata) {
		let desc = `<div style='font-family: Arial, sans-serif;'>`;

		if (metadata.title) {
			desc += `<h3>${metadata.title}</h3>`;
		}

		if (metadata.overview) {
			desc += `<p><strong>Plot:</strong> ${metadata.overview.substring(0, 200)}...</p>`;
		}

		if (metadata.director) {
			desc += `<p><strong>Director:</strong> ${metadata.director}</p>`;
		}

		if (metadata.actors && metadata.actors.length > 0) {
			desc += `<p><strong>Cast:</strong> ${metadata.actors.slice(0, 5).join(', ')}</p>`;
		}

		if (metadata.genres && metadata.genres.length > 0) {
			desc += `<p><strong>Genre:</strong> ${metadata.genres.join(', ')}</p>`;
		}

		if (metadata.runtime) {
			desc += `<p><strong>Runtime:</strong> ${metadata.runtime} minutes</p>`;
		}

		desc += `<p><strong>Condition:</strong> ${formData.condition}</p>`;
		desc += `<p><strong>Format:</strong> Blu-ray</p>`;
		desc += `<p><strong>Region:</strong> Region 1 (US/Canada)</p>`;
		desc += `<p>Fast shipping with tracking. Returns accepted within 30 days.</p>`;
		desc += `</div>`;

		return desc;
	}

	function validateForm() {
		const validationErrors = [];

		if (!formData.title?.trim()) {
			validationErrors.push('Listing title is required');
		}

		if (!formData.s3Url) {
			validationErrors.push('Please upload image to AWS first');
		}

		if (!formData.price || parseFloat(formData.price) <= 0) {
			validationErrors.push('Valid price is required');
		}

		if (!formData.quantity || parseInt(formData.quantity) <= 0) {
			validationErrors.push('Valid quantity is required');
		}

		return validationErrors;
	}

	function transformToBluerayItem() {
		return {
			title: formData.title,
			condition: formData.condition,
			photos: [formData.s3Url],
			metadata: {
				title: formData.movieTitle || formData.title,
				release_date: formData.releaseYear ? `${formData.releaseYear}-01-01` : null,
				genres: [formData.genre, formData.subGenre].filter(Boolean),
				director: formData.director,
				actors: formData.actors ? formData.actors.split(',').map(a => a.trim()) : [],
				studio: formData.studio,
				rating: formData.rating,
				runtime: formData.runtime ? parseInt(formData.runtime) : null,
				overview: null
			},
			price_data: {
				average_price: formData.averagePrice ? parseFloat(formData.averagePrice) : null,
				shipping_cost: formData.shippingCost ? parseFloat(formData.shippingCost) : null,
				total_cost: formData.totalCost ? parseFloat(formData.totalCost) : null,
				comparable_listings: []
			},
			user_notes: formData.userNotes,
			custom_fields: {
				price: parseFloat(formData.price),
				quantity: parseInt(formData.quantity),
				description: formData.description,
				location: formData.location,
				region_code: formData.regionCode,
				language: formData.language,
				case_type: formData.caseType,
				features: formData.features
			}
		};
	}

	function handleSubmit() {
		errors.submit = '';

		// Validate form
		const validationErrors = validateForm();
		if (validationErrors.length > 0) {
			errors.submit = validationErrors.join('; ');
			return;
		}

		// Transform to BlurayItem
		const item = transformToBluerayItem();

		// Mark as submitted
		isSubmitted = true;

		// Call parent callback
		if (onSubmit) {
			onSubmit(item);
		}
	}
</script>

<style>
	.movie-form {
		display: grid;
		gap: 20px;
	}

	.image-preview {
		width: 200px;
		height: auto;
		border-radius: 8px;
		margin-bottom: 15px;
	}

	.form-section {
		padding: 15px;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		background: #fafafa;
	}

	.form-section h3 {
		margin: 0 0 15px 0;
		color: #333;
		font-size: 16px;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}

	.form-group {
		display: flex;
		flex-direction: column;
	}

	.form-group label {
		font-weight: 500;
		margin-bottom: 5px;
		color: #555;
	}

	.form-group input,
	.form-group select,
	.form-group textarea {
		padding: 8px 12px;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-size: 14px;
	}

	.form-group input:focus,
	.form-group select:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: #007bff;
		box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
	}

	.action-buttons {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
		margin-top: 15px;
	}

	.btn {
		padding: 10px 20px;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 14px;
		font-weight: 500;
		transition: background-color 0.2s;
	}

	.btn-primary {
		background: #007bff;
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: #0056b3;
	}

	.btn-success {
		background: #28a745;
		color: white;
	}

	.btn-success:hover:not(:disabled) {
		background: #1e7e34;
	}

	.btn-warning {
		background: #ffc107;
		color: #212529;
	}

	.btn-warning:hover:not(:disabled) {
		background: #e0a800;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-submit {
		background: #17a2b8;
		color: white;
		font-size: 16px;
		padding: 12px 30px;
	}

	.btn-submit:hover:not(:disabled) {
		background: #138496;
	}

	.error {
		color: #dc3545;
		font-size: 12px;
		margin-top: 5px;
	}

	.submit-section {
		margin-top: 20px;
		padding: 20px;
		background: #f8f9fa;
		border-radius: 8px;
		border: 2px solid #17a2b8;
	}

	.submit-success {
		background: #d4edda;
		border-color: #28a745;
		padding: 15px;
		border-radius: 4px;
		color: #155724;
		text-align: center;
	}

	.success-indicator {
		color: #28a745;
		font-size: 12px;
		margin-left: 8px;
	}

	.loading {
		opacity: 0.7;
	}

	.s3-url {
		word-break: break-all;
		font-family: monospace;
		background: #f8f9fa;
		padding: 5px;
		border-radius: 3px;
		font-size: 12px;
	}
</style>

<div class="movie-form">
	<!-- Image Preview -->
	<div>
		<img src={image.url} alt={image.title} class="image-preview" />
		<p><strong>Original File:</strong> {image.originalFilename}</p>
	</div>

	<!-- Action Buttons -->
	<div class="action-buttons">
		<button
			class="btn btn-primary"
			on:click={fetchMetadata}
			disabled={loading.metadata}
			class:loading={loading.metadata}
		>
			{loading.metadata ? 'Fetching...' : 'Fill Metadata'}
		</button>

		<button
			class="btn btn-warning"
			on:click={fetchPricing}
			disabled={loading.pricing}
			class:loading={loading.pricing}
		>
			{loading.pricing ? 'Fetching...' : 'Fill Pricing'}
		</button>

		<button
			class="btn btn-success"
			on:click={uploadToAWS}
			disabled={loading.upload}
			class:loading={loading.upload}
		>
			{loading.upload ? 'Uploading...' : 'Upload to AWS'}
		</button>

		{#if formData.s3Url}
			<span class="success-indicator">✓ Uploaded</span>
		{/if}
	</div>

	<!-- Error Messages -->
	{#if errors.metadata}
		<div class="error">{errors.metadata}</div>
	{/if}
	{#if errors.pricing}
		<div class="error">{errors.pricing}</div>
	{/if}
	{#if errors.upload}
		<div class="error">{errors.upload}</div>
	{/if}

	<!-- Basic Information -->
	<div class="form-section">
		<h3>Basic Information</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="title-{movieIndex}">Listing Title</label>
				<input
					id="title-{movieIndex}"
					type="text"
					bind:value={formData.title}
					placeholder="Movie title for listing"
				/>
			</div>

			<div class="form-group">
				<label for="condition-{movieIndex}">Condition</label>
				<select id="condition-{movieIndex}" bind:value={formData.condition}>
					<option value="New">New</option>
					<option value="Like New">Like New</option>
					<option value="Very Good">Very Good</option>
					<option value="Good">Good</option>
					<option value="Acceptable">Acceptable</option>
					<option value="Used">Used</option>
				</select>
			</div>

			<div class="form-group">
				<label for="price-{movieIndex}">Price ($)</label>
				<input
					id="price-{movieIndex}"
					type="number"
					step="0.01"
					bind:value={formData.price}
					placeholder="12.99"
				/>
			</div>

			<div class="form-group">
				<label for="quantity-{movieIndex}">Quantity</label>
				<input
					id="quantity-{movieIndex}"
					type="number"
					bind:value={formData.quantity}
					placeholder="1"
				/>
			</div>
		</div>
	</div>

	<!-- Movie Metadata -->
	<div class="form-section">
		<h3>Movie Information</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="movie-title-{movieIndex}">Movie Title</label>
				<input
					id="movie-title-{movieIndex}"
					type="text"
					bind:value={formData.movieTitle}
					placeholder="Official movie title"
				/>
			</div>

			<div class="form-group">
				<label for="studio-{movieIndex}">Studio</label>
				<input
					id="studio-{movieIndex}"
					type="text"
					bind:value={formData.studio}
					placeholder="Warner Bros, Disney, etc."
				/>
			</div>

			<div class="form-group">
				<label for="genre-{movieIndex}">Genre</label>
				<input
					id="genre-{movieIndex}"
					type="text"
					bind:value={formData.genre}
					placeholder="Action, Drama, Comedy"
				/>
			</div>

			<div class="form-group">
				<label for="director-{movieIndex}">Director</label>
				<input
					id="director-{movieIndex}"
					type="text"
					bind:value={formData.director}
					placeholder="Director name"
				/>
			</div>

			<div class="form-group">
				<label for="actors-{movieIndex}">Main Actors</label>
				<input
					id="actors-{movieIndex}"
					type="text"
					bind:value={formData.actors}
					placeholder="Actor names (comma separated)"
				/>
			</div>

			<div class="form-group">
				<label for="year-{movieIndex}">Release Year</label>
				<input
					id="year-{movieIndex}"
					type="number"
					bind:value={formData.releaseYear}
					placeholder="2023"
				/>
			</div>

			<div class="form-group">
				<label for="rating-{movieIndex}">MPAA Rating</label>
				<select id="rating-{movieIndex}" bind:value={formData.rating}>
					<option value="G">G</option>
					<option value="PG">PG</option>
					<option value="PG-13">PG-13</option>
					<option value="R">R</option>
					<option value="NC-17">NC-17</option>
					<option value="NR">Not Rated</option>
				</select>
			</div>

			<div class="form-group">
				<label for="runtime-{movieIndex}">Runtime (minutes)</label>
				<input
					id="runtime-{movieIndex}"
					type="number"
					bind:value={formData.runtime}
					placeholder="120"
				/>
			</div>
		</div>
	</div>

	<!-- Technical Specifications -->
	<div class="form-section">
		<h3>Technical Specifications</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="region-{movieIndex}">Region Code</label>
				<select id="region-{movieIndex}" bind:value={formData.regionCode}>
					<option value="1">Region 1 (US/Canada)</option>
					<option value="2">Region 2 (Europe)</option>
					<option value="3">Region 3 (Asia)</option>
					<option value="0">Region Free</option>
				</select>
			</div>

			<div class="form-group">
				<label for="language-{movieIndex}">Language</label>
				<input
					id="language-{movieIndex}"
					type="text"
					bind:value={formData.language}
					placeholder="English"
				/>
			</div>

			<div class="form-group">
				<label for="case-{movieIndex}">Case Type</label>
				<select id="case-{movieIndex}" bind:value={formData.caseType}>
					<option value="Standard Blu-ray Case">Standard Blu-ray Case</option>
					<option value="Steelbook">Steelbook</option>
					<option value="Digipak">Digipak</option>
					<option value="Slip Cover">Slip Cover</option>
				</select>
			</div>

			<div class="form-group">
				<label for="features-{movieIndex}">Special Features</label>
				<input
					id="features-{movieIndex}"
					type="text"
					bind:value={formData.features}
					placeholder="Director Commentary, Deleted Scenes, etc."
				/>
			</div>
		</div>
	</div>

	<!-- Pricing Information -->
	<div class="form-section">
		<h3>Pricing Information</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="avg-price-{movieIndex}">Average Market Price</label>
				<input
					id="avg-price-{movieIndex}"
					type="text"
					bind:value={formData.averagePrice}
					placeholder="Filled by pricing research"
					readonly
				/>
			</div>

			<div class="form-group">
				<label for="shipping-{movieIndex}">Shipping Cost</label>
				<input
					id="shipping-{movieIndex}"
					type="number"
					step="0.01"
					bind:value={formData.shippingCost}
					placeholder="4.99"
				/>
			</div>

			<div class="form-group">
				<label for="total-cost-{movieIndex}">Total Market Cost</label>
				<input
					id="total-cost-{movieIndex}"
					type="text"
					bind:value={formData.totalCost}
					placeholder="Calculated automatically"
					readonly
				/>
			</div>
		</div>
	</div>

	<!-- AWS Upload Status -->
	{#if formData.s3Url}
		<div class="form-section">
			<h3>AWS Upload Status</h3>
			<div class="form-group">
				<label>S3 URL</label>
				<div class="s3-url">{formData.s3Url}</div>
			</div>
		</div>
	{/if}

	<!-- Description -->
	<div class="form-section">
		<h3>Description</h3>
		<div class="form-group">
			<label for="description-{movieIndex}">eBay Listing Description (HTML)</label>
			<textarea
				id="description-{movieIndex}"
				bind:value={formData.description}
				rows="10"
				placeholder="Auto-generated from metadata or enter custom description"
			></textarea>
		</div>
	</div>

	<!-- User Notes -->
	<div class="form-section">
		<h3>Additional Notes</h3>
		<div class="form-group">
			<label for="notes-{movieIndex}">User Notes</label>
			<textarea
				id="notes-{movieIndex}"
				bind:value={formData.userNotes}
				rows="3"
				placeholder="Any additional notes about this item"
			></textarea>
		</div>
	</div>

	<!-- Submit Section -->
	{#if !isSubmitted}
		<div class="submit-section">
			<h3>Ready to Submit?</h3>
			<p>Make sure you've uploaded the image to AWS and filled out all required fields.</p>
			<button
				class="btn btn-submit"
				on:click={handleSubmit}
			>
				Submit & Next
			</button>
			{#if errors.submit}
				<div class="error" style="margin-top: 10px; font-size: 14px;">
					<strong>Error:</strong> {errors.submit}
				</div>
			{/if}
		</div>
	{:else}
		<div class="submit-success">
			<h3>✓ Item Submitted Successfully!</h3>
			<p>This item will be included in your CSV export.</p>
		</div>
	{/if}
</div>