import React, { useEffect, useState } from 'react';
import {
  ApplianceResponse,
  BillResponse,
  confirmAppliance,
  fetchAppliances,
  markServiceDone,
  uploadBill,
} from '../api/assets';
import { getLabel } from '../lib/labels.js';

export const Assets: React.FC = () => {
  const [appliances, setAppliances] = useState<ApplianceResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Upload & Review state
  const [uploading, setUploading] = useState(false);
  const [extractedBill, setExtractedBill] = useState<BillResponse | null>(null);

  // Review Form fields
  const [productName, setProductName] = useState('');
  const [brand, setBrand] = useState('');
  const [modelNumber, setModelNumber] = useState('');
  const [seller, setSeller] = useState('');
  const [price, setPrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');
  const [warrantyMonths, setWarrantyMonths] = useState('12');
  const [categoryId, setCategoryId] = useState('1'); // Default 1 (AC)

  const loadAppliances = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAppliances();
      setAppliances(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load appliances');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppliances();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      const bill = await uploadBill(file);
      setExtractedBill(bill);

      // Pre-fill form from extraction
      const ext = bill.extraction_json || {};
      setProductName(String(ext.product_name?.value || ''));
      setBrand(String(ext.brand?.value || ''));
      setModelNumber(String(ext.model_number?.value || ''));
      setSeller(String(ext.seller?.value || ''));
      setPrice(ext.price?.value ? String(ext.price.value) : '');

      let pDate = String(ext.purchase_date?.value || '');
      if (pDate.includes('/')) {
        const parts = pDate.split('/');
        if (parts.length === 3) {
          pDate = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }
      }
      setPurchaseDate(pDate || new Date().toISOString().split('T')[0]);
      setWarrantyMonths(String(ext.warranty_months?.value || '12'));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to upload bill');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName || !purchaseDate) {
      setError('Product name and purchase date are required.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const ext = extractedBill?.extraction_json || {};
      const corrected: Record<string, unknown> = {};
      if (ext.product_name && ext.product_name.value !== productName) corrected.product_name = productName;
      if (ext.brand && ext.brand.value !== brand) corrected.brand = brand;
      if (ext.price && String(ext.price.value) !== price) corrected.price = price;
      if (ext.purchase_date && ext.purchase_date.value !== purchaseDate) corrected.purchase_date = purchaseDate;

      await confirmAppliance({
        bill_id: extractedBill?.bill_id || null,
        category_id: parseInt(categoryId, 10),
        product_name: productName,
        brand: brand || null,
        model_number: modelNumber || null,
        seller: seller || null,
        price: price ? parseFloat(price) : null,
        purchase_date: purchaseDate,
        warranty_months: parseInt(warrantyMonths, 10) || 0,
        corrected_fields: Object.keys(corrected).length > 0 ? corrected : null,
      });

      setExtractedBill(null);
      await loadAppliances();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to confirm appliance');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleServiceComplete = async (serviceId: number) => {
    try {
      await markServiceDone(serviceId);
      await loadAppliances();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Assets & Bills</h1>
          <p className="text-sm text-slate-500">
            Upload bills, review AI extractions, track warranties, and view automated service schedules.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Bill Upload Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Upload Appliance Bill</h2>
        <p className="text-sm text-slate-500 mb-4">
          Supported formats: PDF, JPG, PNG (Max 10MB). Text and key details will be extracted automatically.
        </p>
        <div className="flex items-center gap-4">
          <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors">
            {uploading ? 'Processing Bill...' : 'Choose File to Upload'}
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              disabled={uploading}
              onChange={handleFileUpload}
            />
          </label>
          {uploading && <span className="text-sm text-slate-500">Extracting fields with confidence scores...</span>}
        </div>
      </div>

      {/* Extracted Bill Review Modal / Card */}
      {extractedBill && (
        <div className="bg-indigo-50 border border-indigo-200 p-6 rounded-xl shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-lg font-semibold text-indigo-950">Review & Correct Extracted Details</h2>
              <p className="text-xs text-indigo-700">
                Parse Status: <span className="font-semibold">{getLabel(extractedBill.parse_status)}</span>. You can edit any field before confirming.
              </p>
            </div>
            <button
              onClick={() => setExtractedBill(null)}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              Cancel
            </button>
          </div>

          <form onSubmit={handleConfirm} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Product Name * {extractedBill.extraction_json?.product_name && (
                  <span className="text-xs font-normal text-slate-500">
                    (Conf: {(extractedBill.extraction_json.product_name.confidence * 100).toFixed(0)}%)
                  </span>
                )}
              </label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Brand</label>
              <input
                type="text"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Model Number</label>
              <input
                type="text"
                value={modelNumber}
                onChange={(e) => setModelNumber(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Seller</label>
              <input
                type="text"
                value={seller}
                onChange={(e) => setSeller(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Price (₹)</label>
              <input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Purchase Date *</label>
              <input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Warranty (Months)</label>
              <input
                type="number"
                value={warrantyMonths}
                onChange={(e) => setWarrantyMonths(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Category (for Service Intervals)</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full text-sm p-2 border border-slate-300 rounded-lg bg-white"
              >
                <option value="1">Air Conditioner (6mo interval)</option>
                <option value="2">Refrigerator (12mo interval)</option>
                <option value="3">Washing Machine (12mo interval)</option>
                <option value="4">Water Purifier / RO (6mo interval)</option>
                <option value="5">Geyser (12mo interval)</option>
                <option value="6">Chimney (6mo interval)</option>
              </select>
            </div>

            <div className="md:col-span-2 flex justify-end gap-3 mt-2">
              <button
                type="submit"
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-5 rounded-lg text-sm"
              >
                Confirm & Create Service Schedule
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Appliances List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <h2 className="font-semibold text-slate-900">Your Appliances & Protection ({appliances.length})</h2>
          <button
            onClick={loadAppliances}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Refresh
          </button>
        </div>

        {loading && appliances.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-400">Loading appliances...</div>
        ) : appliances.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-400">
            No appliances registered yet. Upload a bill above to track warranties and maintenance.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {appliances.map((appliance) => (
              <div key={appliance.appliance_id} className="p-5 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-base">{appliance.product_name}</h3>
                    <p className="text-xs text-slate-500">
                      {appliance.brand && <span>{appliance.brand} • </span>}
                      Purchased: {appliance.purchase_date}
                      {appliance.price && <span> • ₹{Number(appliance.price).toLocaleString('en-IN')}</span>}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Warranty to {appliance.warranty_end_date}
                    </span>
                  </div>
                </div>

                {/* Services Schedule */}
                {appliance.services && appliance.services.length > 0 && (
                  <div className="mt-3 bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                      Scheduled Maintenance Services ({appliance.services.length})
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                      {appliance.services.map((svc) => (
                        <div
                          key={svc.service_id}
                          className="bg-white p-2.5 rounded border border-slate-200 text-xs flex justify-between items-center"
                        >
                          <div>
                            <div className="font-medium text-slate-800">Due: {svc.due_date}</div>
                            <div className="text-slate-400 text-[10px]">
                              {svc.guidance_label === 'general' ? 'General Guidance' : 'Manufacturer'}
                            </div>
                          </div>
                          <div>
                            {svc.status === 'done' ? (
                              <span className="text-emerald-600 font-semibold text-[11px]">Completed</span>
                            ) : (
                              <button
                                onClick={() => handleServiceComplete(svc.service_id)}
                                className="px-2 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded text-[11px] font-medium"
                              >
                                Mark Done
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
