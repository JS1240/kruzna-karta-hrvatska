import React, { useEffect, useState } from 'react';

export const MapboxTest: React.FC = () => {
  const [tokenStatus, setTokenStatus] = useState<'loading' | 'valid' | 'invalid'>('loading');
  const [tokenInfo, setTokenInfo] = useState<any>(null);

  useEffect(() => {
    const testToken = async () => {
      const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
      
      if (!token) {
        setTokenStatus('invalid');
        return;
      }

      try {
        const response = await fetch(`https://api.mapbox.com/v1/tokens/validate?access_token=${token}`);
        const data = await response.json();
        
        if (response.ok && data.valid) {
          setTokenStatus('valid');
          setTokenInfo(data);
        } else {
          setTokenStatus('invalid');
          setTokenInfo(data);
        }
      } catch (error) {
        setTokenStatus('invalid');
        setTokenInfo({ error: error.message });
      }
    };

    testToken();
  }, []);

  return (
    <div className="bg-gray-100 p-4 rounded-lg">
      <h3 className="font-bold mb-2">Mapbox Token Test</h3>
      <div className="text-sm">
        <p><strong>Status:</strong> {tokenStatus}</p>
        {tokenInfo && (
          <pre className="mt-2 p-2 bg-gray-200 rounded text-xs overflow-auto">
            {JSON.stringify(tokenInfo, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};