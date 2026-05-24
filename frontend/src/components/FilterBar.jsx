import React from "react";

function FilterBar({ search, setSearch, status, setStatus }) {
  return (
    <div className="row g-2 mb-3 bg-white p-3 rounded shadow-sm border">
      <div className="col-md-8">
        <input type="text" className="form-control" placeholder="🔍 Tìm tên sinh viên cần tra cứu..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>
      <div className="col-md-4">
        <select className="form-select" value={status} onChange={e => setStatus(e.target.value)}>
          <option value="all">🌐 Tất cả kết quả</option>
          <option value="pass">🟢 Trạng thái: ĐẬU</option>
          <option value="fail">🔴 Trạng thái: HỌC LẠI</option>
        </select>
      </div>
    </div>
  );
}

export default FilterBar;