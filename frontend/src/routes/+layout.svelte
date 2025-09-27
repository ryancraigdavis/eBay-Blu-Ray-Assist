<style>
	:global(body) {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		margin: 0;
		padding: 20px;
		background-color: #f5f5f5;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
	}

	header {
		background: white;
		padding: 20px;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		margin-bottom: 20px;
	}

	h1 {
		margin: 0;
		color: #333;
	}
</style>

<div class="container">
	<header>
		<h1>eBay Blu-ray Assistant</h1>
		<p>Upload your Blu-ray images to generate eBay listings automatically</p>
	</header>
	<main>
		<slot />
	</main>
</div>