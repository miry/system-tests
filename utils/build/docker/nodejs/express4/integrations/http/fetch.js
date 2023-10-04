module.exports = {
  doWork: async ({ url, payload }) => {
    return fetch(
      url,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }
    )
  }
}