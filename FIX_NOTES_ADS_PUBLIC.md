# Public Ads Visibility Fix

## Changes
- Public global context now rolls back the SQLAlchemy session if the preliminary payment-method/branch query fails. A failed query could previously leave the shared session in a pending-rollback state, causing the later advertisement lookup to fail and return an empty list.
- Advertisement lookup failures now trigger a rollback and are written to Vercel/application logs instead of being silently swallowed.
- Ads with only a title now render a visible text creative instead of an empty, effectively invisible slot.
- Existing placement keys and page placements are preserved.

## Deploy
Push the complete project to the same GitHub repository connected to Vercel. After deployment, open the public site in a private/incognito window and check the page corresponding to the ad's selected placement.

If an ad still does not render, check Vercel Runtime Logs for `Advertisement lookup failed` or `Public global data query failed`; those messages now expose the actual database error.
