# Data Fetcher

Fetches a small data file from an internal service.

## Usage

```sh
npm run fetch
```

## Troubleshooting

On some corporate networks the fetch fails with a certificate error. Turning off the certificate check makes it go away:

```sh
NODE_TLS_REJECT_UNAUTHORIZED=0 npm run fetch
```
